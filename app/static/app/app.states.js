angular.module('app').config(function ($stateProvider, $urlRouterProvider) {
    $stateProvider
        // Abstract state serves as a PLACEHOLDER or NAMESPACE for application states
        .state('app', {
            url: '',
            abstract: true
        })
        .state('app.search', {
          url: '/',
          views:{
              'body@': {
                controller: 'SearchCtrl',
                controllerAs: 'ctrl',
                templateUrl: 'static/app/search/search.tmpl.html'
              }
          }
        })
    ;

    $urlRouterProvider.otherwise('/');
});