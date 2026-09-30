import logger from "./logger";
import type { Request, Response, NextFunction } from "express";

const asyncHandler = (fn: any) => {
    return (req: Request, res: Response, next: NextFunction) => {
        Promise.resolve(fn(req, res, next)).catch((err: any) => {
            logger.error(
                `Error: ${err.message} with stack trace: ${err.stack} and req body ${req.body} and req params ${req.params} and req query ${req.query} from ${req.ip} on ${req.url}`
            );
            next(err);
        });
    };
};

export default asyncHandler;