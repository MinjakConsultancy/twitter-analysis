const db = require("../models");
const Word = db.word;
var assert = require('assert');

exports.findAllNotSpecified = (req, res) => {
    const filter = {
      '$and': [{
        '$or': [
          {
            'sentiment': -1
          }, {
            'sentiment': {
              '$exists': false
            }
          }
        ]
      },
      {
        '$or': [
          {
            'pos': 'ADV'
          }, {
            'pos': 'NOUN'
          }
        ]
      },
      ]
    };
    const sort = {'count':-1}
    Word.find(filter)  
        .limit(10)
        .sort(sort)
        .select("-c")
        .exec()
        .then(data => {
            res.send(data)
        })       
    
};

exports.findOne = (req, res) => {
  
};

exports.update = (req, res) => {
  var myWord = new Word(req.body);
  const filterOne = {
      '_id': req.body.id
  };
  const update = {
    'sentiment': myWord.sentiment,
    'denial': myWord.denial,
  };
  console.log('update word '+req.body.id);
  Word.findOneAndUpdate(filterOne
    , update
    ).then(item => {
      res.sendStatus(200) // equivalent to res.status(200).send('OK')
      //res.send("item saved to database");
    })
    .catch(err => {
      console.log(err);
      res.status(400).send("unable to save to database");
    });
};

exports.findAllPublished = (req, res) => {
  
};