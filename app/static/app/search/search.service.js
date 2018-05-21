angular.module('search')
  .service('SearchService', function SearchService($http) {
    this.getTopics = function getTopics() {
      return $http.get('/topics');
    };
  })
;