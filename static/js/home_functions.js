$(document).ready(function(){
    $("#btn_log_off").on('click',function(){
        console.log("click boton cerrar sesion");
        $.ajax({
            url:'/auth/logout',
            data:'aaa',
            type:'POST',
            success:function(response){
                console.log(response);
            },
            error:function(error){
                console.log(error);
            }
        });
    });
});
