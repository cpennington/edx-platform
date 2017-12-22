'use strict'

const path = require('path')
const webpack = require('webpack')

const providePlugin = new webpack.ProvidePlugin({
  'jQuery': 'jquery',
  '$': 'jquery',
  'window.jQuery': 'jquery'
})

module.exports = {
  'entry': {
    'course_search/js/course_search_factory': './openedx/features/course_search/static/course_search/js/course_search_factory.js',
    'learner_profile/js/learner_profile_factory': './openedx/features/learner_profile/static/learner_profile/js/learner_profile_factory.js',
    'course_bookmarks/js/course_bookmarks_factory': './openedx/features/course_bookmarks/static/course_bookmarks/js/course_bookmarks_factory.js',
    'course_bookmarks/js/views/bookmark_button': './openedx/features/course_bookmarks/static/course_bookmarks/js/views/bookmark_button.js',
    'js/capa/drag_and_drop/main': './common/static/js/capa/drag_and_drop/main.js',
    'ova': './common/static/js/vendor/ova/ova.js',
  },
  'resolve': {
    'modules': [
      path.resolve(__dirname, '../common/static/js/vendor'),
      path.resolve(__dirname, '../common/static/common/js/vendor'),
      path.resolve(__dirname, '../common/static/common/js/vendor/ova'),
      path.resolve(__dirname, '../common/static/js/src'),
      path.resolve(__dirname, '../common/static/')
    ],
    'alias': {
      'annotator_1.2.9': 'edxnotes/annotator-full.min',
      'annotator-harvardx': 'ova/annotator-full-firebase-auth',
      'annotator': 'ova/annotator-full',
      'backbone-relational': 'backbone-relational.min',
      'backbone-super': 'js/vendor/backbone-super',
      'backbone.associations': 'backbone-associations-min',
      'catch': 'ova/catch/js/catch',
      'codemirror': 'codemirror-compressed',
      'codemirror/stex': 'CodeMirror/stex',
      'datepair': 'timepicker/datepair',
      'handlebars': 'ova/catch/js/handlebars-1.1.2',
      'jquery.fileupload-process': 'jQuery-File-Upload/js/jquery.fileupload-process',
      'jquery.fileupload-validate': 'jQuery-File-Upload/js/jquery.fileupload-validate',
      'jquery.fileupload': 'jQuery-File-Upload/js/jquery.fileupload',
      'jquery.flot': 'flot/jquery.flot.min',
      'jquery.iframe-transport': 'jQuery-File-Upload/js/jquery.iframe-transport',
      'jquery.inputnumber': 'html5-input-polyfills/number-polyfill',
      'jquery.markitup': 'markitup/jquery.markitup',
      'jquery.qtip': 'jquery.qtip.min',
      'jquery.smoothScroll': 'jquery.smooth-scroll.min',
      'jquery.timepicker': 'timepicker/jquery.timepicker',
      'jquery.tinymce': 'tinymce/js/tinymce/jquery.tinymce.min',
      'jquery.ui': 'jquery-ui.min',
      'jquery.url': 'url.min',
      'moment': 'moment-with-locales',
      'moment-timezone': 'moment-timezone-with-data',
      'osda': 'OpenSeaDragonAnnotation',
      'picturefill': 'common/js/vendor/picturefill',
      'text': 'requirejs/text',
      'tinymce': 'tinymce/js/tinymce/tinymce.full.min',
      'URI': 'URI.min',
    }
  },
  'plugins': [
    providePlugin
  ],
  'module': {
    'loaders': [
      {
        'test': /annotator_1.2.9/,
        'loader': 'exports?Annotator!imports?jquery'
      },
      {
        'test': /date/,
        'loader': 'exports?Date'
      },
      {
        'test': /jquery/,
        'loader': 'exports?jQuery'
      },
      {
        'test': /jquery.cookie/,
        'loader': 'exports?jQuery.fn.cookie!imports?jquery'
      },
      {
        'test': /jquery.timeago/,
        'loader': 'exports?jQuery.timeago!imports?jquery'
      },
      {
        'test': /jquery.url/,
        'loader': 'exports?jQuery.url!imports?jquery'
      },
      {
        'test': /jquery.fileupload/,
        'loader': 'exports?jQuery.fn.fileupload!imports?jquery.ui,jquery.iframe-transport'
      },
      {
        'test': /jquery.tinymce/,
        'loader': 'exports?jQuery.fn.tinymce!imports?jquery,tinymce'
      },
      {
        'test': /backbone.paginator/,
        'loader': 'exports?Backbone.PageableCollection!imports?backbone'
      },
      {
        'test': /backbone-super/,
        'loader': 'exports?undefined!imports?backbone'
      },
      {
        'test': /string_utils/,
        'loader': 'exports?interpolate_text!imports?underscore'
      },
      {
        'test': /video.dev/,
        'loader': 'exports?videojs'
      },
      {
        'test': /vjs.youtube/,
        'loader': 'exports?undefined!imports?video.dev'
      },
      {
        'test': /rangeslider/,
        'loader': 'exports?undefined!imports?video.dev'
      },
      {
        'test': /annotator/,
        'loader': 'exports?Annotator'
      },
      {
        'test': /annotator-harvardx/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /share-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /richText-annotator/,
        'loader': 'exports?undefined!imports?annotator,tinymce'
      },
      {
        'test': /reply-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /tags-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /diacritic-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /flagging-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /grouping-annotator/,
        'loader': 'exports?undefined!imports?annotator'
      },
      {
        'test': /ova/,
        'loader': 'exports?ova!imports?annotator,annotator-harvardx,video.dev,vjs.youtube,rangeslider,share-annotator,richText-annotator,reply-annotator,tags-annotator,flagging-annotator,grouping-annotator,diacritic-annotator,jquery-Watch,catch,handlebars,URI'
      },
      {
        'test': /osda/,
        'loader': 'exports?osda!imports?annotator,annotator-harvardx,video.dev,vjs.youtube,rangeslider,share-annotator,richText-annotator,reply-annotator,tags-annotator,flagging-annotator,grouping-annotator,diacritic-annotator,openseadragon,jquery-Watch,catch,handlebars,URI'
      },
      {
        'test': /tinymce/,
        'loader': 'exports?tinymce'
      },
      {
        'test': /moment/,
        'loader': 'exports?moment'
      },
      {
        'test': /moment-timezone/,
        'loader': 'exports?moment!imports?moment'
      },
      {
        'test': /draggabilly/,
        'loader': 'exports?Draggabilly'
      },
      {
        'test': /hls/,
        'loader': 'exports?Hls'
      }
    ]
  }
}
