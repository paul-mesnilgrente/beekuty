$(function() {
  // element argument can be a selector string
  //   for an individual element
  var $grid = $('.grid').masonry({
    // options
    itemSelector: '.grid-item',
    columnWidth: '.grid-sizer',
    percentPosition: true,
    gutter: '.gutter-sizer'
  });

  // layout Masonry after each image loads
  $grid.imagesLoaded().progress(function() {
    $grid.masonry('layout');
  });
})
