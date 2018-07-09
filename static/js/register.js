$(document).ready(function(){
    var me = this;
    //-------------- Registrar empresa -----------------------

    //afterrender
    $("#win_register_company").on('shown.bs.modal',function(){
        console.log("afterrender");

        //me.validRegisterForm=false;
    });
    //al cerrar modal de registrar empresa
    $("#win_register_company").on('hidden.bs.modal',function(){
        //Quitar clases agregadas a alerta
        $("#alertRCForm").removeClass("alert-warning");
        $("#alertRCForm").removeClass("alert-danger");
        $("#alertRCForm").addClass("alert-info");
        $("#alertRCForm").css("display","none"); //Ocultar alerta
        $("#alertRCForm").find('p').html("Ocurrió un error."); //Cambiar mensaje a alerta
        //Resetear formulario
        resetForm("#frmRegisterCompany",["input|INPUT"]);

        //$("#frmRegisterCompany")[0].reset();
    });


    //Valida campo business_name
    //keyup
    $("#RCbusiness_name").on('focusout',function(){
        emptyField("#RCbusiness_name","#spnRCbusiness_name");
    });

    $("#RCname").on('focusout',function(){
        emptyField("#RCname","#spnRCname");
    });
    $("#RCaddress").on('focusout',function(){
        emptyField("#RCaddress","#spnRCaddress");
    });
    $("#RCphone").on('focusout',function(){
        emptyField("#RCphone","#spnRCphone");
    });

    //botón guardar empresa
    $("#btnSaveRegisterCompany").on('click',function(){
        //validar campos
        var input_list=$("#frmRegisterCompany").find("input"); //regresa todos los input y el elemento padre
        var is_valid=true;
        for (x in input_list){
            if (input_list[x].nodeName=='INPUT'){ //solo se toman en cuenta los input
                if ($("#"+input_list[x].id).hasClass('valid-field')==false) {
                    is_valid=false;
                }
            }
        }
        if (is_valid){
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            });
            var data=getDictForm("#frmRegisterCompany",[]);
            $.ajax({
                url:'/register/saveNewCompany',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response1, response2, response3){
                    console.log("success");
                    var response=JSON.parse(response1); //parsea response de petición ajax
                    EasyLoading.hide();
                    if (response.success){
                        $("#alertLayout").find('p').html(response.msg_response);
                        $("#win_register_company").modal("hide");
                        $("#alertLayout").css("display","block");
                    }
                    else{
                        $("#alertRCForm").removeClass("alert-info");
                        $("#alertRCForm").removeClass("alert-success");
                        $("#alertRCForm").addClass("alert-danger");
                    }
                    $("#alertRCForm").find('p').html(response.msg_response);
                    $("#alertRCForm").css("display","block");
                },
                error:function(error1,error2,error3){
                    EasyLoading.hide();
                    $("#alertRCForm").removeClass("alert-info");
                    $("#alertRCForm").removeClass("alert-success");
                    $("#alertRCForm").addClass("alert-danger");
                    // $("#alertRCForm").removeClass("alert-info").addClass("alert-warning");
                    $("#alertRCForm").css("display","block");
                }
            });
        }
        else{
            $("#alertRCForm").removeClass("alert-info");
            $("#alertRCForm").removeClass("alert-danger");
            $("#alertRCForm").addClass("alert-warning");
            $("#alertRCForm").find('p').html("¡Existen campos vacíos!<br>Debe completar el formulario para registrar la nueva empresa.");
            $("#alertRCForm").css("display","block");
        }
    });

    //botón salir ventana nueva empresa
    $("#btnCloseRegisterCompany").on('click',function(){
        $("#win_register_company").modal("hide"); //oculta modal
    });

    //--------------------------------- Registrar usuario administrador/consultor-------------------------

    //boton salir ventana nuevo usuario admin / consultor
    $("#btnCloseRegAdminUser").on('click',function(){
        $("#win_new_admin_user").modal("hide");
    });

    //afterrender win user admin
    $("#win_new_admin_user").on('shown.bs.modal',function(){
        console.log("afterrender user admin");
        $.ajax({
            url:'/register/getCompanies',
            data:JSON.stringify({'company_id':-1}), //-1 -> todas
            method:'POST',
            success:function(response1){
                var response=JSON.parse(response1);
                if(response.success){
                    var items=response.data;
                    $.each(items, function (i, item) {
                        $('#NAUcompany_id').append($('<option>', {
                            //value: item.name,
                            text : item.name,
                            name : item.company_id
                        }));
                    });
                    $.ajax({
                        url:'/register/getUserType',
                        data:JSON.stringify({'get':'admin'}),
                        method:'POST',
                        success:function(user_response){
                            var resp=JSON.parse(user_response);
                            if (resp.success){
                                var items=resp.data;
                                $.each(items,function(i, item){
                                    $("#NAUuser_type_id").append($('<option>',{
                                        //value:item.user_type,
                                        text:item.user_type,
                                        name:item.user_type_id
                                    }));
                                });
                            }
                        }
                    });
                }
                else{
                    console.log("Error");
                    $("#alertNAUForm").find("span").html(response.msg_response);
                    $("#alertNAUForm").css("display","block");
                }
            },
            error:function(error){
                console.log(error);
                $("#alertNAUForm").css("display","block");
            }
        });

    });
    $("#win_new_admin_user").on('hidden.bs.modal',function(){
        console.log("cerrar");
        resetForm("#frmNewAdminUser",["input|INPUT","select|SELECT"]);
    });
    $("#chkNAUshow_password").click(function(){
        if ($("#chkNAUshow_password")[0].checked){
            $("#NAUpassword").attr("type","text");
        }
        else{
            $("#NAUpassword").attr("type","password");
        }
    });
    $("#chkNAUshow_confirm_password").click(function(){
        if ($("#chkNAUshow_confirm_password")[0].checked){
            $("#NAUconfirm_password").attr("type","text");
        }
        else{
            $("#NAUconfirm_password").attr("type","password");
        }
    });

    $("#NAUname").focusout(function(){
        var valIsEmpty=emptyField("#NAUname","#spnNAUname");
        if (valIsEmpty){
            minLen("#NAUname","#spnNAUname",3);
        }
    });

    $("#NAUlogin").focusout(function(){
        var valIsEmpty=emptyField("#NAUlogin","#spnNAUlogin");
        if (valIsEmpty){
            var valMinLen=minLen("#NAUlogin","#spnNAUlogin",5);
            if (valMinLen){
                noSpaces("#NAUlogin","#spnNAUlogin");
            }
        }
    });

    $("#NAUemail").focusout(function(){
        var valIsEmpty=emptyField("#NAUemail","#spnNAUemail");
        if (valIsEmpty){
            var valNoSpaces=noSpaces("#NAUemail","#spnNAUemail");
            if (valNoSpaces){
                validateMail("#NAUemail","#spnNAUemail");
            }
        }
    });

    $("#btnSaveRegAdminUser").click(function(){
        var input_list=$("#frmNewAdminUser").find(":input");
        var is_valid=true;
        $("#NAUname").focusout();
        $("#NAUlogin").focusout();
        $("#NAUemail").focusout();
        for (x in input_list){
            if (input_list[x].type=='text'){
                if ($("#"+input_list[x].id).hasClass('valid-field')===false){
                    $("#"+input_list[x].id).focusout();
                    console.log(input_list[x].id);
                    is_valid=false;
                }
            }
        }
        if (is_valid){
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            });
            var sel_list=[{'id':"#NAUcompany_id",'name':'company_id'},{'id':"#NAUuser_type_id",'name':'user_type_id'}];
            var frm=getDictForm("#frmNewAdminUser",sel_list);
            frm['user_id']=-1;
            console.log(frm);
            $.ajax({
                url:'/register/createUser',
                method:'POST',
                data:JSON.stringify(frm),
                success:function(response){
                    var res=JSON.parse(response);
                    EasyLoading.hide();
                    if (res.success){
                        setMessage("#alertLayout",[],"",res.msg_response,true);
                        $("#win_new_admin_user").modal("hide");
                    }
                    else{
                        setMessage("#alertNAUForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(error){
                    EasyLoading.hide();
                    setMessage("#alertNAUForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
                }
            });
        }
        else{
            setMessage("#alertNAUForm",["alert-info","alert-success"],"alert-danger","Existen campos incorrectos o incompletos, favor de revisar.",true);
        }
    });


});


// //Funcion que obtiene datos de un formulario y los regresa en forma de diccionario, se envía id del formulario y en caso de contener select, una lista con diccionarios: {id,name}
// function getDictForm(formId,select_list){
//     //var frmId='#'+formId;
//     var frm = $(formId).serializeArray().reduce(function(obj, item) {
//         obj[item.name] = item.value;
//         return obj;
//     }, {});
//     console.log(select_list);
//     for (x in select_list){
//         frm[select_list[x]['name']]=parseInt($(select_list[x]['id']).find("option:selected").attr("name"));
//     }
//     return frm;
// };
//
// //Función prueba para ocultar objecto
// $(function(){
//     $("[data-hide]").on("click", function(){
//         $(this).closest("." + $(this).attr("data-hide")).hide();
//     });
// });
//
// function emptyField(fieldId,spanId){
//     var valid=false;
//     var input=$(fieldId);
//     var is_name=input.val();
//     if(is_name && (input[0].value.trim()).length>0){ //valida si es diferente de vacio y verifica que no tenga puros espacios vacios
//         input.removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg").addClass("error-msg");
//         valid=true;
//     }
//     else{
//         input.removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg").addClass("show-error-msg");
//         $(spanId).html("Este campo es requerido.");
//     }
//     return valid;
// }
//
// //formId-> id del formulario a resetear, input_type-> lista con los nodeName de los input que contiene el formulario
// function resetForm(formId,input_type){
//     console.log("reset form "+formId);
//     $(formId)[0].reset();
//     for (x in input_type){
//         var node_name=input_type[x].split("|")[1];
//         var input_list=$(formId).find(input_type[x].split("|")[0]);
//         for (i in input_list){
//             if (input_list[i].nodeName==node_name){ //solo se toman en cuenta los input
//                 if ($("#"+input_list[i].id).hasClass('valid-field')){
//                     $("#"+input_list[i].id).removeClass('valid-field');
//                 }
//                 if ($("#"+input_list[i].id).hasClass('invalid-field')){
//                     $("#"+input_list[i].id).removeClass('invalid-field');
//                 }
//                 if ($("#spn"+input_list[i].id).hasClass('show-error-msg')){
//                     $("#spn"+input_list[i].id).removeClass("show-error-msg").addClass("error-msg");
//                 }
//                 if ($("#spn"+input_list[i].id).hasClass('show-error-msg-row')){
//                     $("#spn"+input_list[i].id).removeClass("show-error-msg-row").addClass("error-msg-row");
//                     $("#spn"+input_list[i].id).html("Error");
//                 }
//
//                 if (node_name=='SELECT'){
//                     $("#"+input_list[i].id).empty(); //vacia un select
//                 }
//             }
//         }
//     }
// }
//
// //funcion para mostrar alerta
// //alertId=id de la alerta, rmv_list=lista de clases que se deben remover
// //add=clase que se va a agregar, msg=mensaje a mostrar
// function setMessage(alertId,rmv_list,add,msg,show){
//     for (x in rmv_list){
//         $(alertId).removeClass(rmv_list[x]);
//     }
//     $(alertId).addClass(add);
//     $(alertId).find('p').html(msg);
//     if (show===true){
//         $(alertId).css("display","block");
//     }
//     else{
//         $(alertId).css("display","none");
//     }
//
// }
