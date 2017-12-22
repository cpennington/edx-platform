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
    'course_search/js/course_search_factory': 'course_search/js/course_search_factory',
    'course_search/js/dashboard_search_factory': 'course_search/js/dashboard_search_factory',
    'discussion/js/discussion_profile_page_factory': 'discussion/js/discussion_profile_page_factory',
    'js/api_admin/catalog_preview_factory': 'js/api_admin/catalog_preview_factory',
    'js/certificates/factories/certificate_invalidation_factory': 'js/certificates/factories/certificate_invalidation_factory',
    'js/certificates/factories/certificate_whitelist_factory': 'js/certificates/factories/certificate_whitelist_factory',
    'js/course_sharing/course_sharing_events': 'js/course_sharing/course_sharing_events',
    'js/courseware/accordion_events': 'js/courseware/accordion_events',
    'js/courseware/course_info_events': 'js/courseware/course_info_events',
    'js/courseware/courseware_factory': 'js/courseware/courseware_factory',
    'js/courseware/toggle_element_visibility': 'js/courseware/toggle_element_visibility',
    'js/dateutil_factory': './lms/static/js/dateutil_factory',
    'js/discovery/discovery_factory': 'js/discovery/discovery_factory',
    'js/discussions_management/views/discussions_dashboard_factory': 'js/discussions_management/views/discussions_dashboard_factory',
    'js/edxnotes/views/notes_visibility_factory': 'js/edxnotes/views/notes_visibility_factory',
    'js/edxnotes/views/page_factory': 'js/edxnotes/views/page_factory',
    'js/financial-assistance/financial_assistance_form_factory': 'js/financial-assistance/financial_assistance_form_factory',
    'js/groups/views/cohorts_dashboard_factory': 'js/groups/views/cohorts_dashboard_factory',
    'js/header_factory': 'js/header_factory',
    'js/learner_dashboard/program_details_factory': 'js/learner_dashboard/program_details_factory',
    'js/learner_dashboard/program_list_factory': 'js/learner_dashboard/program_list_factory',
    'js/learner_dashboard/unenrollment_factory': 'js/learner_dashboard/unenrollment_factory',
    'js/student_account/logistration_factory': 'js/student_account/logistration_factory',
    'js/student_account/views/account_settings_factory': 'js/student_account/views/account_settings_factory',
    'js/student_account/views/finish_auth_factory': 'js/student_account/views/finish_auth_factory',
    'js/views/message_banner': 'js/views/message_banner',
    'lms/js/preview/preview_factory': 'lms/js/preview/preview_factory',
    'support/js/certificates_factory': 'support/js/certificates_factory',
    'support/js/enrollment_factory': 'support/js/enrollment_factory',
    'teams/js/teams_tab_factory': 'teams/js/teams_tab_factory',
    'discussion/js/discussion_board_factory': 'discussion/js/discussion_board_factory',
    'js/edxnotes/views/notes_visibility_factory': './lms/static/js/edxnotes/views/notes_visibility_factory.js',
  },
  'resolve': {
    'modules': ['lms/static'],
    'alias': {
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
