"use strict";

angular.module('search')
  .filter('multiHighlight', function() {
    return function(input, pairs) {
      var out = '';
      var ranges = [];
      var i = 0;
      pairs.forEach( function (pair) {
        if(!pair.exclude){
          i = 0;
          var indexes = [];
          // Find all occurrences of the search value in the input string
          while(true) {
            var index = input.indexOf(pair.value, i);
            if(index === -1){
              break;
            }
            indexes.push(index);
            i = index + 1;
          }
          // For each occurrence determine what range should be highlighted
          indexes.forEach( function (idx) {
            var range = [idx, idx + pair.value.length];
            var inserted = false;
            i = 0;
            while(i < ranges.length){
              // Check for overlap with preexisting ranges
              if(
                (range[0] > ranges[i] && range[0] < ranges[i+1]) ||
                (range[0] === ranges[i]) || (range[0] === ranges[i + 1]) ||
                (range[1] > ranges[i] && range[1] < ranges[i+1]) ||
                (range[1] === ranges[i]) || (range[1] === ranges[i + 1]) ||
                (range[0] < ranges[i] && range[1] > ranges[i + 1])
              ){
                ranges.splice(i, 2, Math.min(range[0], ranges[i]), Math.max(range[1], ranges[i+1]));
                inserted = true;
                break;
              }
              i += 2;
            }
            if(!inserted){
              ranges.push(range[0], range[1]);
            }
          });
        }
      });
      if(!ranges.length){
        return input;
      }
      // Generate the highlighted output string
      ranges.sort(function(a, b) {
        return a - b;
      });
      i = 0;
      out += input.slice(0, ranges[0]);
      while(i < ranges.length){
        out += '<span class="highlight">' + input.slice(ranges[i], ranges[i+1]) + '</span>';
        out += input.slice(ranges[i+1], (((i + 2) >= ranges.length)? input.length : ranges[i+2]));
        i += 2;
      }
      return out;
    };
  })
;