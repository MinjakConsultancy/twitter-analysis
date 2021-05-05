module.exports = mongoose => {
    var schema = mongoose.Schema(
        {
          word: String,
          pos: String,
          sentiment: Number,
          count: Number,
          denial: Boolean
        },
        { timestamps: true }
      )

    schema.method("toJSON", function() {
        const { __v, _id, ...object } = this.toObject();
        object.id = _id;
        return object;
      });
    
    mongoose.set('debug', true);
  
    const word = mongoose.model(
      "word",schema, "word");
  
    return word;
  };