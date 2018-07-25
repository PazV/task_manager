$(document).ready(function(){
    var me = this;
    this.user_info=JSON.parse($("#spnSession")[0].textContent);

    $("#chkChPwshow_old_pass").click(function(){
        if ($("#chkChPwshow_old_pass")[0].checked){
            $("#ChPwold_pass").attr("type","text");
        }
        else{
            $("#ChPwold_pass").attr("type","password");
        }
    });
    $("#chkChPwshow_new_pass").click(function(){
        if ($("#chkChPwshow_new_pass")[0].checked){
            $("#ChPwnew_pass").attr("type","text");
        }
        else{
            $("#ChPwnew_pass").attr("type","password");
        }
    });
    $("#chkChPwshow_confirm_pass").click(function(){
        if ($("#chkChPwshow_confirm_pass")[0].checked){
            $("#ChPwconfirm_new_pass").attr("type","text");
        }
        else{
            $("#ChPwconfirm_new_pass").attr("type","password");
        }
    });

    $("#btnSavePasswordChange").click(function(){
        var input_list=$("#frmChangePassword").find("input");
        var is_valid=true;
        for (x in input_list){
            if (input_list[x].nodeName=='INPUT' && input_list[x].type!="checkbox"){
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
            var data=getDictForm("#frmChangePassword",[]);
            var g=JSON.parse($("#spnSession")[0].textContent);
            data['user_id']=g.user_id;

            $.ajax({
                url:'/users/changePassword',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    EasyLoading.hide();
                    var res=JSON.parse(response);
                    if (res.success){
                        setMessage("#alertLayout",[],"",res.msg_response,true);
                        $("#win_change_pass").modal("hide");
                    }
                    else{
                        setMessage("#alertChPwForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(error){
                    EasyLoading.hide();
                    setMessage("#alertChPwForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
                }
            });
        }
        else{
            setMessage("#alertChPwForm",["alert-success","alert-info"],"alert-danger","<h5><b>¡Atención!</b></h5><p>Existen campos inválidos, favor de revisar.</p>",true);
        }
    });

    $("#btnClosePasswordChange").click(function(){
        $("#win_change_pass").modal("hide");
        resetForm("#frmChangePassword",["input|INPUT"]);
        setMessage("#alertChPwForm",["alert-success","alert-danger"],"alert-info","",false);
        $("#chkChPwshow_old_pass").prop("checked",false);
        $("#chkChPwshow_new_pass").prop("checked",false);
        $("#chkChPwshow_confirm_pass").prop("checked",false);
        $("#ChPwconfirm_new_pass").attr("type","password");
        $("#ChPwnew_pass").attr("type","password");
        $("#ChPwold_pass").attr("type","password");
    });

    $("#ChPwold_pass").focusout(function(){
        var emptyFieldValid = emptyField("#ChPwold_pass","#spnChPwold_pass");

        if (emptyFieldValid){
            var minLenValid = minLen("#ChPwold_pass","#spnChPwold_pass",6);
            if (minLenValid){
                noSpaces("#ChPwold_pass", "#spnChPwold_pass");
            }
        }

    });
    $("#ChPwnew_pass").focusout(function(){
        var emptyFieldValid = emptyField("#ChPwnew_pass","#spnChPwnew_pass");
        if (emptyFieldValid){
            var minLenValid = minLen("#ChPwnew_pass","#spnChPwnew_pass",6);
            if (minLenValid){
                noSpaces("#ChPwnew_pass","#spnChPwnew_pass");
            }
        }
    });
    $("#ChPwconfirm_new_pass").focusout(function(){
        var emptyFieldValid = emptyField("#ChPwconfirm_new_pass","#spnChPwconfirm_new_pass");
        if (emptyFieldValid){
            var minLenValid = minLen("#ChPwconfirm_new_pass","#spnChPwconfirm_new_pass",6);
            if (minLenValid){
                var noSpacesValid = noSpaces("#ChPwconfirm_new_pass","#spnChPwconfirm_new_pass");
                if (noSpacesValid){
                    if ($("#ChPwnew_pass")[0].value!=$("#ChPwconfirm_new_pass")[0].value){
                        $("#ChPwconfirm_new_pass").removeClass("valid-field").addClass("invalid-field");
                        $("#spnChPwconfirm_new_pass").removeClass("error-msg").addClass("show-error-msg");
                        $("#spnChPwconfirm_new_pass").html("Las contraseñas ingresadas no coinciden.");
                    }
                    else{
                        $("#ChPwconfirm_new_pass").removeClass("invalid-field").addClass("valid-field");
                        $("#spnChPwconfirm_new_pass").removeClass("show-error-msg").addClass("error-msg");
                    }
                }
            }
        }
    });



    $("#win_admin_users").on("show.bs.modal",function(){
        $("#grdAdminUsers").DataTable({
            "scrollY": "255px",
            "scrollCollapse":true,
            serverSide:true,
            ajax:{
                data:{'company_id':me.user_info.company_id},
                url:'/users/getUsers',
                dataSrc:'data',
                type:'POST'
            },
            columns:[
                {data:'name',"width":"40%"},
                {data:'login',"width":"15%"},
                {data:'user_type',"width":"15%"},
                {data:'email',"width":"30%"}
            ]
        });
        //$("#grdAdminUsers").DataTable().columns.adjust();
        // $("#grdAdminUsers").DataTable().draw();
        if ($("#grdAdminUsers").is(":visible")){
            console.log("visible");
        }
        $.fn.dataTable.tables( { visible: true, api: true } ).columns.adjust();
    });

    $("#grdAdminUsers").is(":visible");


    $("#btnNewUser").click(function(){
        me.new_user=true;
        $("#spnNUtitle").html("Nuevo usuario");
        $.ajax({
            url:'/register/getUserType',
            data:JSON.stringify({'get':'all'}),
            method:'POST',
            success:function(response){
                var res=JSON.parse(response);
                var items=res.data;
                $.each(items,function(i, item){
                    $("#NUuser_type_id").append($('<option>',{
                        text:item.user_type,
                        name:item.user_type_id
                    }));
                });
            }
        });
        $("#win_new_user").modal("show");
    });

    $("#NUname").focusout(function(){
        var valIsEmpty=emptyField("#NUname","#spnNUname");
        if (valIsEmpty){
            minLen("#NUname","#spnNUname",3);
        }
    });
    $("#NUlogin").focusout(function(){
        var valIsEmpty=emptyField("#NUlogin","#spnNUlogin");
        if (valIsEmpty){
            var valMinLen=minLen("#NUlogin","#spnNUlogin",5);
            if (valMinLen){
                noSpaces("#NUlogin","#spnNUlogin");
            }
        }
    });
    $("#NUemail").focusout(function(){
        var valIsEmpty=emptyField("#NUemail","#spnNUemail");
        if (valIsEmpty){
            var valNoSpaces=noSpaces("#NUemail","#spnNUemail");
            if (valNoSpaces){
                validateMail("#NUemail","#spnNUemail");
            }
        }
    });

    $("#btnSaveNewUser").click(function(){
        var input_list=$("#frmNewUser").find('input');
        var is_valid=true;
        $("#NUname").focusout();
        $("#NUlogin").focusout();
        $("#NUemail").focusout();
        for (x in input_list){
            if (input_list[x].nodeName=='INPUT'){
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
            var sel_list=[{'id':"#NUuser_type_id",'name':"user_type_id"}];
            var data=getDictForm("#frmNewUser",sel_list);
            data['company_id']=me.user_info.company_id;
            if (me.new_user){
                data['user_id']=-1
            }
            else{
                var ind=$("#grdAdminUsers").DataTable().row('.selected').index(); //índice de fila seleccionada
                var record=$("#grdAdminUsers").DataTable().rows(ind).data()[0]; //obtener record seleccionado
                data['user_id']=record['user_id'];
            }
            $.ajax({
                url:'/register/createUser',
                data:JSON.stringify(data),
                method:'POST',
                success:function(response){
                    EasyLoading.hide();
                    var res=JSON.parse(response);
                    if (res.success){
                        setMessage("#alertAdminUsersWin",[],"",res.msg_response,true);
                        $("#win_new_user").modal("hide");
                        $("#grdAdminUsers").DataTable({
                            "scrollY": "255px",
                            "scrollCollapse":true,
                            serverSide:true,
                            ajax:{
                                data:{'company_id':me.user_info.company_id},
                                url:'/users/getUsers',
                                dataSrc:'data',
                                type:'POST'
                            },
                            columns:[
                                {data:'name',"width":"40%"},
                                {data:'login',"width":"15%"},
                                {data:'user_type',"width":"15%"},
                                {data:'email',"width":"30%"}
                            ]
                        });
                    }
                    else{
                        setMessage("#alertNUForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(error){
                    EasyLoading.hide();                    setMessage("#alertNUForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo nuevamente.",true);
                }
            });
        }
        else{
            setMessage("#alertNUForm",["alert-success","alert-info"],"alert-danger","<h5><b>¡Atención!</b></h5><p>Existen campos inválidos, favor de revisar.</p>",true);
        }
    });

    $("#win_new_user").on('hidden.bs.modal',function(){
        resetForm("#frmNewUser",["input|INPUT","select|SELECT"]);
        $("#NUlogin").attr("readonly",false);
    });

    $("#win_change_pass").on('hidden.bs.modal',function(){
        resetForm("#frmChangePassword",["input|INPUT","checkbox|CHECKBOX"]);

    });

    $('#grdAdminUsers').DataTable().on( 'select', function ( e, dt, type, index ) {
        var record = $('#grdAdminUsers').DataTable().rows(index).data()[0];
        console.log(record);
    } );

    $("#btnEditUser").click(function(){
        me.new_user=false;
        $("#NUlogin").attr("readonly",true);
        var table=$("#grdAdminUsers").DataTable();
        if (table.rows('.selected').any()){ //si existe un registro seleccionado
            var ind=table.row('.selected').index(); //índice de fila seleccionada
            var data=table.rows(ind).data()[0]; //obtener record seleccionado
            $.ajax({
                url:'/register/getUserType',
                data:JSON.stringify({'get':'all'}),
                method:'POST',
                success:function(response){
                    var res=JSON.parse(response);
                    var items=res.data;
                    $.each(items,function(i, item){
                        if (item.user_type_id==data['user_type_id']){
                            $("#NUuser_type_id").append($('<option>',{
                                text:item.user_type,
                                name:item.user_type_id,
                                selected:true
                            }));
                        }
                        else{
                            $("#NUuser_type_id").append($('<option>',{
                                text:item.user_type,
                                name:item.user_type_id,
                                selected:false
                            }));
                        }});
                }
            });
            $("#spnNUtitle").html("Editar usuario");
            var frm=$("#frmNewUser");
            $.each(data, function(key, value){
                $('[name='+key+']', frm).val(value);
            });
            //para cuando son varios select, usar find('select') y obtener id's para ir asignando valor a cada uno

            var input_list=frm.find("input");
            for (x in input_list){
                if (input_list[x].nodeName=='INPUT'){
                    $("#"+input_list[x].id).addClass("valid-field");
                }
            }

            $("#win_new_user").modal("show");
        }
        else{
            setMessage("#alertAdminUsersWin",["alert-success","alert-danger"],"alert-info","<h5><b>¡Atención!</b></h5><p>Debe seleccionar un usuario para editarlo.</p>",true);
        }
    });

    $("#btnCloseNewUser").click(function(){
        $("#win_new_user").modal("hide");

    });

    $("#btnDisableUser").click(function(){
        var table=$("#grdAdminUsers").DataTable();
        if (table.rows('.selected').any()){
            $.confirm({
                theme:'dark',
                title: 'Atención',
                content: '¿Está seguro de deshabilitar este usuario?',
                buttons: {
                    confirm:{
                        text:'Sí',
                        action: function () {
                            $.alert('Confirmed!');
                        }
                    },
                    cancel:{
                        text:'No',
                        action:function () {
                            $.alert('Canceled!');
                        }
                    }
                    // somethingElse: {
                    //     text: 'Something else',
                    //     btnClass: 'btn-blue',
                    //     keys: ['enter', 'shift'],
                    //     action: function(){
                    //         $.alert('Something else?');
                    //     }
                    // }
                }
            });
        }
    });

});

// function minLen(inputId,spanId,len){
//     var valid=false;
//     var val=$(inputId)[0].value;
//     if (val.length<len){
//         $(inputId).removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg").addClass("show-error-msg");
//         $(spanId).html("Este campo debe tener un mínimo de "+len+" caracteres.");
//     }
//     else{
//         $(inputId).removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg").addClass("error-msg");
//         valid=true;
//     }
//     return valid;
// }
//
// function noSpaces(inputId,spanId){
//     var valid=false;
//     var val=$(inputId)[0].value;
//     var no_space=val.split(" ").join("");
//     if (val!=no_space){
//         $(inputId).removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg").addClass("show-error-msg");
//         $(spanId).html("Este campo no debe contener espacios.");
//     }
//     else{
//         $(inputId).removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg").addClass("error-msg");
//         valid=true;
//     }
//     return valid;
//
// }
//
// function validateMail(inputId,spanId){
//     var valid=false;
//     var val=$(inputId)[0].value;
//     var patt=/^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
//     if (patt.exec(val)==null){
//         $(inputId).removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg").addClass("show-error-msg");
//         $(spanId).html("Debe ingresar una dirección de correo válida.");
//     }
//     else{
//         $(inputId).removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg").addClass("error-msg");
//         valid=true;
//     }
//     return valid;
// }
//
//
$.extend( $.fn.dataTable.defaults, {
    // "responsive":{
    //     "details":false
    // },
    "autoWidth":true,
    "searching":false,
    "ordering":false,
    "destroy":true,
    "select":{
        "style":"single",
        //"blurable":true
    },
    "lengthMenu": [ 5, 10, 15, 20, 25 ],
    "language":{
        "decimal":        ".",
        "emptyTable":     "No hay información disponible",
        "info":           "Mostrando _START_ a _END_ de _TOTAL_ registros",
        "infoEmpty":      "Mostrando 0 a 0 de 0 registros",
        "infoFiltered":   "(filtrado de _MAX_ total registros)",
        "infoPostFix":    "",
        "thousands":      ",",
        "lengthMenu":     "Mostrar _MENU_ registros",
        "loadingRecords": "Cargando...",
        "processing":     "Procesando...",
        "search":         "Buscar:",
        "zeroRecords":    "No se encontraron registros",
        "paginate": {
            "first":      "Primero",
            "last":       "Última",
            "next":       "Siguiente",
            "previous":   "Anterior"
        },
        "aria": {
            "sortAscending":  ": activar para ordenar de forma ascendente",
            "sortDescending": ": activar para ordenar de forma descendente"
        },
        "select":{
            "rows":""
        }
    },
});
