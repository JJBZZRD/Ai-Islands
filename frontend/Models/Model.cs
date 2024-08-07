using System.Collections.Generic;
using System.Text.Json.Serialization;
using frontend.Models;
using Newtonsoft.Json.Linq;

namespace frontend.Models
{
    public class Model
    {
        //Define instance variable with all possible first order keys from library.json

        public Model(JObject json)
        {
            processJson(json);
            
        }

        private void processJson(JObject json)
        {
         // some loop which correctly assigns all first order keys from json to instance variables, copying the data over.
        }
    }
}

Model model = new Model(json);
