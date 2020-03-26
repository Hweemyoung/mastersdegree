for (var m = 0; m < 12; m++) {
    var ct = 0;
    var $divFollowerCount = $('article').filter(function () {
        var d = new Date($(this).children('time').attr('datetime'));
        return (d.getMonth() === m);
    }).find('.follower_count span');
    // console.log($divFollowerCount);
    var $counts = $divFollowerCount.map(function () {
        // console.log($(this).html());
        // if (Number($(this).html()) === NaN){
        //     console.log('NaN:', $(this).html());
        // }
        // ct += Number($(this).html());
        // console.log(this);
        return Number($(this).html().replace(',', ''));
    });
    console.log($counts);
    for (i = 0; i < $counts.length; i++) {
        ct += $counts[i];
    }
    console.log('month=', m + 1, ct);
}