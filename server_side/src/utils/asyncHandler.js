import logger from "./logger.js";
const asyncHandler = (fn) => {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch((err) => {
            logger.error(
                `Error: ${err.message} with stack trace: ${err.stack} and req body ${req.body} and req params ${req.params} and req query ${req.query} from ${req.ip} on ${req.url}`
            );
            next(err);
        });
    };
};

export default asyncHandler;
