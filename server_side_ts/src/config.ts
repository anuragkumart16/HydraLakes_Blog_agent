import dotenv from "dotenv"
dotenv.config()

type Config = {
    port: number,
    node_env: string,
    allowed_origins: string[]
}

const config: Config = {
    port: Number(process.env.PORT) || 8000,
    node_env: process.env.NODE_ENV || "development",
    allowed_origins: process.env.ALLOWED_ORIGINS?.split(",") || []
}

export default config
