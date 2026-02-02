import concurrently from "concurrently"
import waitOn from "wait-on"
import open from "open"

async function main() {
  concurrently(
    [
      { command: "npm --prefix backend run dev", name: "BACKEND" },
      { command: "npm --prefix frontend run dev -- --port 5173", name: "FRONTEND" }
    ],
    { killOthers: ["failure", "success"], prefix: "name" }
  )

  await waitOn({ resources: ["http://localhost:5173", "http://localhost:8000/api/health"] })
  await open("http://localhost:5173")
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
