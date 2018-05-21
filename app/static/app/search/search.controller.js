angular.module('search')
  .controller('SearchCtrl', function SearchCtrl($scope, SearchService) {
    var searchCtrl = this;

    searchCtrl.currentSearch = null;
    searchCtrl.messages = [];
    searchCtrl.matched = 0;
    searchCtrl.topics = [];
    searchCtrl.error = false;
    searchCtrl.source = null;
    searchCtrl.searchParams = new SearchParams({
      'topic': '',
      'type': 'plain',
      'searchPairs': [],
      'limit': 50,
      'stop': false
    });
    searchCtrl.searchParams.addSearchPair();
    searchCtrl.showBoxes = false;
    searchCtrl.searchMetadata = {
      'partitions': -1,
      'total': -1,
      'consumed': -1
    };

    function SearchParams(form) {
      this.topic = form.topic;
      this.type = form.type;
      this.searchPairs = form.searchPairs;
      this.limit = form.limit;
      this.stop = form.stop;

      this.clone = function () {
        var that = {}
        that.topic = this.topic;
        that.type = this.type;
        that.searchPairs = JSON.parse(JSON.stringify(this.searchPairs));
        that.limit = this.limit;
        that.stop = this.stop;

        return new SearchParams(that);
      };

      this.addSearchPair = function () {
        this.searchPairs.push({'key': '', 'value': '', 'exclude': false});
      };

      this.removeSearchPair = function (pair) {
        var index = this.searchPairs.indexOf(pair);
        if(index > -1){
          this.searchPairs.splice(index, 1);
        }
      };

      this.encodedPairs = function () {
        result = '';
        include = this.searchPairs.filter(function (pair) { return !pair.exclude; });
        exclude = this.searchPairs.filter(function (pair) { return pair.exclude; });
        result += '&include=';
        include.forEach(function (pair, index) {
          result += pair.key + '<|,|>' + pair.value;
            if(index < include.length - 1){
              result += '<|;|>';
            }
        });
        result += '&exclude=';
        exclude.forEach(function (pair, index) {
          result += pair.key + '<|,|>' + pair.value;
          if(index < exclude.length - 1){
            result += '<|;|>';
          }
        });
        return result;
      };
    }

    SearchService.getTopics()
      .then(function (response) {
        searchCtrl.topics = response.data;
      });

    var onMessage = function (msg) {
      $scope.$apply(function () {
        var parsedMsg = JSON.parse(msg.data);
        searchCtrl.matched += 1;
        searchCtrl.searchMetadata.consumed = parsedMsg.consumed;
        delete parsedMsg.consumed;
        searchCtrl.messages.unshift(parsedMsg);
        if(searchCtrl.messages.length >= searchCtrl.currentSearch.limit && searchCtrl.currentSearch.stop){
          searchCtrl.stop();
        } else if(searchCtrl.messages.length > searchCtrl.currentSearch.limit && !searchCtrl.currentSearch.stop) {
          searchCtrl.messages.pop();
        }
      });
    };

    var onError = function (msg) {
      $scope.$apply(function () {
        searchCtrl.error = true;
      });
    };

    var onOpen = function (msg) {
      $scope.$apply(function () {
        if(searchCtrl.error){
          searchCtrl.error = false;
          searchCtrl.messages = [];
          searchCtrl.matched = 0;
        }
      });
    };

    var onMetadata = function (msg) {
      $scope.$apply(function () {
        searchCtrl.searchMetadata = JSON.parse(msg.data)
      });
    };

    searchCtrl.stop = function () {
      if(searchCtrl.source !== null){
        searchCtrl.source.removeEventListener('open', onOpen, false);
        searchCtrl.source.removeEventListener('message', onMessage, false);
        searchCtrl.source.removeEventListener('metadata', onMetadata, false);
        searchCtrl.source.removeEventListener('error', onError, false);
        searchCtrl.source.close();
        searchCtrl.source = null;
      }
    };

    searchCtrl.changeSource = function () {
      searchCtrl.stop();
      searchCtrl.currentSearch = searchCtrl.searchParams.clone();
      searchCtrl.messages = [];
      searchCtrl.matched = 0;
      searchCtrl.searchMetadata = {
        'partitions': -1,
        'total': -1,
        'consumed': -1
      }
      searchCtrl.source = new EventSource('/search?topic=' + searchCtrl.currentSearch.topic + '&type=' + searchCtrl.currentSearch.type + searchCtrl.currentSearch.encodedPairs());
      searchCtrl.source.addEventListener('open', onOpen, false);
      searchCtrl.source.addEventListener('message', onMessage, false);
      searchCtrl.source.addEventListener('metadata', onMetadata, false);
      searchCtrl.source.addEventListener('error', onError, false);
    };

    searchCtrl.toCsv = function () {
      var csvContent = 'data:text/csv;charset=utf-8,Timestamp;Partition;Offset;Message\r\n';
      searchCtrl.messages.forEach( function (message) {
        if(message.selected || !searchCtrl.showBoxes){
          csvContent += message.timestamp + ';' + message.partition + ';' + message.offset + ';' + message.value + '\r\n';
        }
      });
      var encodedUri = encodeURI(csvContent);
      var link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", searchCtrl.currentSearch.topic + '-' + Date.now() + '.csv');
      document.body.appendChild(link); // Required for FF

      link.click();
    };

    searchCtrl.toZip = function () {
      var zip = new JSZip();
      var extension = (searchCtrl.currentSearch.type === 'json')? '.json' : '.txt';
      searchCtrl.messages.forEach( function (message) {
        if(message.selected || !searchCtrl.showBoxes){
          var name = message.timestamp + '-' + message.partition + '-' + message.offset + extension;
          zip.file(name, message.value);
        }
      });
      zip.generateAsync({type:'blob'})
        .then(function(content) {
          var name = searchCtrl.currentSearch.topic + '-' + Date.now() + '.zip';
          saveAs(content, name);
        });
    };

    searchCtrl.exportEnabled = function () {
      return (searchCtrl.messages.length > 0 && !searchCtrl.showBoxes) || (searchCtrl.messages.filter(function (msg){return msg.selected}).length > 0);
    };
  })
;