import asyncHandler from "../../utils/asyncHandler";
import type { Request, Response } from "express";


const healthCheckController = asyncHandler(async (req: Request, res: Response) => {
    res.json({
        message: "OK",
        status: "success",
        statusCode: 200,
        data: null,
        ip: req.ip,
        url: req.url,
        method: req.method,
        params: req.params,
        query: req.query,
        body: req.body,
    });
});

export { healthCheckController }