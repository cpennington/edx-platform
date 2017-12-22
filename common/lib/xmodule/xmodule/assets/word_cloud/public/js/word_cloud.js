window.WordCloud = function(el) {
    require(['WordCloudMain'], function(WordCloudMain) {
        new WordCloudMain(el);
    });
};
