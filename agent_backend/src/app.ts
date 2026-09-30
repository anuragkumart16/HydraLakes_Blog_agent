import express from "express"
import cors from "cors"
import config from "./config"

const app = express()

app.use(cors({
    origin: config.allowed_origins,
    credentials: true
}))
app.use(express.json())

import healthCheckRouter from "./v1/healthCheck/route";

app.use("/api/v1/health-check", healthCheckRouter);

export default app;

