angular.module('app', [
    'ngAnimate',
    'ngMaterial',
    'ngMessages',
    'ngSanitize',
    'ui.router',
    'search'
])
.config(function($mdThemingProvider) {
  $mdThemingProvider.theme('default')
    .primaryPalette('indigo')
    .accentPalette('blue-grey');
  $mdThemingProvider.theme('dark')
    .dark();
});
