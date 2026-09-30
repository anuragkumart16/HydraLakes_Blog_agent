const Response = (res,status,message,data) =>{
    res.status(status).json({
        status,
        message,
        data,
        success: status <= 399 ? true : false
    })
}

export default Response