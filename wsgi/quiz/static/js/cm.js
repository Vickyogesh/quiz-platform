function getQuestion() {
    var question_id = $('#cm_question_id').val();
    var quiz_id = $('#cm_quiz_id').val();

    var question_text = $('#cm_question_text');
    var question_expl = $('#cm_question_expl');
    var img_wrap = $("#cm_image_wrap");

    img_wrap.html('');

    if (question_id === ''){
        return
    }

    $.get('/cm/question/'+quiz_id+'/'+question_id, function (data) {
        if (data === 'null'){
            question_text.html("Wrong question id")
        }else {
            question_text.html(question_id + ' | '+data['text']);
            question_expl.val(data['explanation']);
            if (data['image']){
                img_wrap.html('<img class="cm_image">');
                $(".cm_image").attr('src', '/img/'+data['image']+'.jpg')
            }
        }

    })
}

function setExplanation() {
    var question_id = $('#cm_question_id').val();
    var quiz_id = $('#cm_quiz_id').val();
    var expl = $("#cm_question_expl").val();

    $.ajax({
        url: '/cm/question/'+quiz_id+'/'+question_id,
        type: 'PUT',
        data: {'explanation': expl}
    }).success(function (res) {
        success();
    })
}

function success() {
    var success_block = $(".cm_success");
    success_block.slideDown('fast');
    setTimeout(function () {
        success_block.slideUp('fast');
    }, 1000)
}