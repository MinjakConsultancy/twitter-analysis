module.exports = app => {
    const word = require("../controllers/word.controller.js");
  
    var router = require("express").Router();
  
    router.get("/", word.findAll);
  
    router.get("/:id", word.findOne);
  
    router.put("/:id", word.update);
  
    app.use('/api/word', router);
  };