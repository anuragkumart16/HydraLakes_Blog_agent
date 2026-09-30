import app from "./app.js";

const port = process.env.PORT || 3000

import healthCheckRouter from "./routes/healthcheck.routes.js"

app.use('/api/healthcheck',healthCheckRouter)


app.listen(port,()=>{
    console.log(`server is running on port http://localhost:${port}`)
})