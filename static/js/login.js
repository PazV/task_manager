$(document).ready(function(){
    $("#btnForgotPassword").click(function(){
        $("#win_forgot_password").modal("show");
    });

    $("#btnCloseForgotPassword").click(function(){
        $("#win_forgot_password").modal("hide");
    });

    $("#RPlogin").focusout(function(){
        var valIsEmpty=emptyField("#RPlogin","#spnRPlogin");
        if (valIsEmpty){
            noSpaces("#RPlogin","#spnRPlogin");
        }
    });

    $("#RPemail").focusout(function(){
        var valIsEmpty=emptyField("#RPemail","#spnRPemail");
        if (valIsEmpty){
            var valNoSpaces=noSpaces("#RPemail","#spnRPemail");
            if (valNoSpaces){
                validateMail("#RPemail","#spnRPemail");
            }
        }
    });

    $("#btnRecoverPassword").click(function(){
        var input_list=$("#frmRecoverPassword").find(":input");
        var is_valid=true;
        $("#RPemail").focusout();
        $("#RPlogin").focusout();
        for (x in input_list){
            if (input_list[x].type=='text' ){
                if ($("#"+input_list[x].id).hasClass('valid-field')===false){
                    $("#"+input_list[x].id).focusout();
                    console.log(input_list[x].id);
                    is_valid=false;
                }
            }
        }
        if (is_valid){
            EasyLoading.show({
                text:'Cargando...',
                type:EasyLoading.TYPE['PACMAN']
            });
            $.ajax({
                url:'/auth/recoverPassword',
                method:'POST',
                data:JSON.stringify({'login':$("#RPlogin").val(),'email':$("#RPemail").val()}),
                success:function(response){
                    var res=JSON.parse(response);
                    EasyLoading.hide();
                    if (res.success){
                        $("#win_forgot_password").modal("hide");
                        setMessage("#alertLogin",["alert-danger","alert-info"],"alert-success",res.msg_response,true);
                    }
                    else{
                        setMessage("#alertRecoverPassForm",["alert-success","alert-info"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(){
                    EasyLoading.hide();
                    setMessage("#alertRecoverPassForm",["alert-success","alert-info"],"alert-danger","Ocurrió un error, favor de intentarlo nuevamente.",true);
                }
            })
        }
        else{
            setMessage("#alertRecoverPassForm",["alert-success","alert-info"],"alert-danger","<h5><b>¡Atención!</b></h5><p>Existen campos inválidos, favor de revisar.</p>",true);
        }
    });

    $("#win_forgot_password").on('hidden.bs.modal',function(){
        resetForm("#frmRecoverPassword",["input|INPUT"]);
    });

});
