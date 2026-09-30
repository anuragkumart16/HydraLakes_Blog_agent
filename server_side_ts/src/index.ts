import config from "./config";
import express from "express";
import app from "./app";


app.listen(config.port, () => {
    console.log(`Server is running on port http://localhost:${config.port}`)
})