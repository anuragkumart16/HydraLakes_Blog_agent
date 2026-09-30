import asyncHandler from "../utils/asyncHandler.js";
import Response from "../utils/Response.js";
import logger from "../utils/logger.js";

const healthcheck = asyncHandler(async(req,res) => {
    logger.info(`HealthCheck request recieved from ${req.ip}`)
    Response(res,200,"Server is up and Running!",{ip: req.ip})
})

export {healthcheck}