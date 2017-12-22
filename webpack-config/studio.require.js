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
    'js/certificates/factories/certificates_page_factory': './cms/static/js/certificates/factories/certificates_page_factory',
    'js/collections/group': './cms/static/js/collections/group',
    'js/factories/asset_index': './cms/static/js/factories/asset_index.js',
    'js/factories/base': './cms/static/js/factories/base.js',
    'js/factories/container': './cms/static/js/factories/container.js',
    'js/factories/course_create_rerun': './cms/static/js/factories/course_create_rerun.js',
    'js/factories/course_info': './cms/static/js/factories/course_info.js',
    'js/factories/edit_tabs': './cms/static/js/factories/edit_tabs.js',
    'js/factories/export': './cms/static/js/factories/export.js',
    'js/factories/group_configurations': './cms/static/js/factories/group_configurations.js',
    'js/factories/index': './cms/static/js/factories/index.js',
    'js/factories/library': './cms/static/js/factories/library.js',
    'js/factories/manage_users_lib': './cms/static/js/factories/manage_users_lib.js',
    'js/factories/manage_users': './cms/static/js/factories/manage_users.js',
    'js/factories/outline': './cms/static/js/factories/outline.js',
    'js/factories/register': './cms/static/js/factories/register.js',
    'js/factories/settings_advanced': './cms/static/js/factories/settings_advanced.js',
    'js/factories/settings_graders': './cms/static/js/factories/settings_graders.js',
    'js/factories/settings': './cms/static/js/factories/settings.js',
    'js/factories/textbooks': './cms/static/js/factories/textbooks.js',
    'js/factories/videos_index': './cms/static/js/factories/videos_index.js',
    'js/maintenance/force_course_publish': 'js/maintenance/force_publish_course',
    'js/models/asset': './cms/static/js/models/asset',
    'js/models/course': './cms/static/js/models/course',
    'js/sock': './cms/static/js/sock',
    'js/factories/login': './cms/static/js/factories/login.js'
  },
  'resolve': {
    'modules': [
      path.resolve(__dirname, '../cms/static')
    ],
    'alias': {
      'jquery.immediateDescendents': 'coffee/src/jquery.immediateDescendents',
      'xblock/cms.runtime.v1': 'cms/js/xblock/cms.runtime.v1',
      'xblock': 'common/js/xblock',
      'accessibility': 'js/src/accessibility_tools',
      'ieshim': 'js/src/ie_shim',
      'tooltip_manager': 'js/src/tooltip_manager',
      'hls': path.resolve(__dirname, '../cms/static/common/js/vendor/hls'),
      'lang_edx': 'js/src/lang_edx',
      'mathjax': '//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_SVG&delayStartupUntil=configured',
      'youtube': '//www.youtube.com/player_api?noext',
    }
  },
  'plugins': [
    providePlugin
  ],
  'module': {
    'loaders': [
      {
        'test': /gettext/,
        'loader': 'exports?gettext'
      },
      {
        'test': /date/,
        'loader': 'exports?Date'
      },
      {
        'test': /jquery.ui/,
        'loader': 'exports?jQuery.ui!imports?jquery'
      },
      {
        'test': /jquery.form/,
        'loader': 'exports?jQuery.fn.ajaxForm!imports?jquery'
      },
      {
        'test': /jquery.markitup/,
        'loader': 'exports?jQuery.fn.markitup!imports?jquery'
      },
      {
        'test': /jquery.leanmodal/,
        'loader': 'exports?jQuery.fn.leanModal!imports?jquery'
      },
      {
        'test': /jquery.ajaxQueue/,
        'loader': 'exports?jQuery.fn.ajaxQueue!imports?jquery'
      },
      {
        'test': /jquery.smoothScroll/,
        'loader': 'exports?jQuery.fn.smoothScroll!imports?jquery'
      },
      {
        'test': /jquery.cookie/,
        'loader': 'exports?jQuery.fn.cookie!imports?jquery'
      },
      {
        'test': /jquery.qtip/,
        'loader': 'exports?jQuery.fn.qtip!imports?jquery'
      },
      {
        'test': /jquery.scrollTo/,
        'loader': 'exports?jQuery.fn.scrollTo!imports?jquery'
      },
      {
        'test': /jquery.flot/,
        'loader': 'exports?jQuery.fn.plot!imports?jquery'
      },
      {
        'test': /jquery.fileupload/,
        'loader': 'exports?jQuery.fn.fileupload!imports?jquery.ui,jquery.iframe-transport'
      },
      {
        'test': /jquery.fileupload-process/,
        'loader': 'exports?undefined!imports?jquery.fileupload'
      },
      {
        'test': /jquery.fileupload-validate/,
        'loader': 'exports?undefined!imports?jquery.fileupload'
      },
      {
        'test': /jquery.inputnumber/,
        'loader': 'exports?jQuery.fn.inputNumber!imports?jquery'
      },
      {
        'test': /jquery.tinymce/,
        'loader': 'exports?jQuery.fn.tinymce!imports?jquery,tinymce'
      },
      {
        'test': /datepair/,
        'loader': 'exports?undefined!imports?jquery.ui,jquery.timepicker'
      },
      {
        'test': /underscore/,
        'loader': 'exports?_'
      },
      {
        'test': /backbone/,
        'loader': 'exports?Backbone!imports?underscore,jquery'
      },
      {
        'test': /backbone.associations/,
        'loader': 'exports?Backbone.Associations!imports?backbone'
      },
      {
        'test': /backbone.paginator/,
        'loader': 'exports?Backbone.PageableCollection!imports?backbone'
      },
      {
        'test': /youtube/,
        'loader': 'exports?YT'
      },
      {
        'test': /codemirror/,
        'loader': 'exports?CodeMirror'
      },
      {
        'test': /codemirror\/stex/,
        'loader': 'exports?undefined!imports?codemirror'
      },
      {
        'test': /tinymce/,
        'loader': 'exports?tinymce'
      },
      {
        'test': /lang_edx/,
        'loader': 'exports?undefined!imports?jquery'
      },
      {
        'test': /mathjax/,
        'loader': 'exports?MathJax'
      },
      {
        'test': /URI/,
        'loader': 'exports?URI'
      },
      {
        'test': /tooltip_manager/,
        'loader': 'exports?undefined!imports?jquery,underscore'
      },
      {
        'test': /jquery.immediateDescendents/,
        'loader': 'exports?undefined!imports?jquery'
      },
      {
        'test': /xblock\/core/,
        'loader': 'exports?XBlock!imports?jquery,jquery.immediateDescendents'
      },
      {
        'test': /xblock\/runtime.v1/,
        'loader': 'exports?XBlock!imports?xblock/core'
      },
      {
        'test': /cms\/js\/main/,
        'loader': 'exports?undefined!imports?coffee/src/ajax_prefix'
      },
      {
        'test': /js\/src\/logger/,
        'loader': 'exports?Logger!imports?coffee/src/ajax_prefix'
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
      }
    ]
  }
}
