import { Router } from "express";
import { healthCheckController } from "./controller";

const router = Router()

router.route("/").get(healthCheckController)

export default router