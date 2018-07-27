//Funcion que obtiene datos de un formulario y los regresa en forma de diccionario, se envía id del formulario y en caso de contener select, una lista con diccionarios: {id,name}
function getDictForm(formId,select_list){
    //var frmId='#'+formId;
    var frm = $(formId).serializeArray().reduce(function(obj, item) {
        obj[item.name] = item.value;
        return obj;
    }, {});
    console.log(select_list);
    for (x in select_list){
        frm[select_list[x]['name']]=parseInt($(select_list[x]['id']).find("option:selected").attr("name"));
    }
    return frm;
};

//Función prueba para ocultar objecto
$(function(){
    $("[data-hide]").on("click", function(){
        $(this).closest("." + $(this).attr("data-hide")).hide();
    });
});

function emptyField(fieldId,spanId){
    var valid=false;
    var input=$(fieldId);
    var is_name=input.val();
    if(is_name && (input[0].value.trim()).length>0){ //valida si es diferente de vacio y verifica que no tenga puros espacios vacios
        input.removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg").addClass("error-msg");
        valid=true;
    }
    else{
        input.removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg").addClass("show-error-msg");
        $(spanId).html("Este campo es requerido.");
    }
    return valid;
}

//formId-> id del formulario a resetear, input_type-> lista con los nodeName de los input que contiene el formulario
function resetForm(formId,input_type){
    console.log("reset form "+formId);
    $(formId)[0].reset();
    for (x in input_type){
        var node_name=input_type[x].split("|")[1];
        var input_list=$(formId).find(input_type[x].split("|")[0]);
        for (i in input_list){
            if (input_list[i].nodeName==node_name){ //solo se toman en cuenta los input
                if ($("#"+input_list[i].id).hasClass('valid-field')){
                    $("#"+input_list[i].id).removeClass('valid-field');
                }
                if ($("#"+input_list[i].id).hasClass('invalid-field')){
                    $("#"+input_list[i].id).removeClass('invalid-field');
                }
                if ($("#spn"+input_list[i].id).hasClass('show-error-msg')){
                    $("#spn"+input_list[i].id).removeClass("show-error-msg").addClass("error-msg");
                }
                if ($("#spn"+input_list[i].id).hasClass('show-error-msg-row')){
                    $("#spn"+input_list[i].id).removeClass("show-error-msg-row").addClass("error-msg-row");
                    $("#spn"+input_list[i].id).html("Error");
                }

                if (node_name=='SELECT'){
                    $("#"+input_list[i].id).empty(); //vacia un select
                }
            }
        }
    }
}

//funcion para mostrar alerta
//alertId=id de la alerta, rmv_list=lista de clases que se deben remover
//add=clase que se va a agregar, msg=mensaje a mostrar
function setMessage(alertId,rmv_list,add,msg,show){
    for (x in rmv_list){
        $(alertId).removeClass(rmv_list[x]);
    }
    $(alertId).addClass(add);
    $(alertId).find('p').html(msg);
    if (show===true){
        $(alertId).css("display","block");
    }
    else{
        $(alertId).css("display","none");
    }

}



function emptyFieldRow(fieldId,spanId){
    var valid=false;
    var input=$(fieldId);
    var is_name=input.val();
    if(is_name && (input[0].value.trim()).length>0){ //valida si es diferente de vacio y verifica que no tenga puros espacios vacios
        input.removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg-row").addClass("error-msg-row");
        $(spanId).html("Error");
        valid=true;
    }
    else{
        input.removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg-row").addClass("show-error-msg-row");
        $(spanId).html("Este campo es requerido.");
    }
    return valid;
}

function hasExtension(inputID, exts) {
    var fileName = document.getElementById(inputID).value;
    return (new RegExp('(' + exts.join('|').replace(/\./g, '\\.') + ')$')).test(fileName);
}

function maxLenRow(inputId,spanId,len){
    var valid=false;
    var val=$(inputId)[0].value;
    if (val.length>len){
        $(inputId).removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg-row").addClass("show-error-msg-row");
        $(spanId).html("Este campo puede tener un máximo de "+len+" caracteres.");
    }
    else{
        $(inputId).removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg-row").addClass("error-msg-row");
        valid=true;
    }
    return valid;
}

function minLen(inputId,spanId,len){
    var valid=false;
    var val=$(inputId)[0].value;
    if (val.length<len){
        $(inputId).removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg").addClass("show-error-msg");
        $(spanId).html("Este campo debe tener un mínimo de "+len+" caracteres.");
    }
    else{
        $(inputId).removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg").addClass("error-msg");
        valid=true;
    }
    return valid;
}

function noSpaces(inputId,spanId){
    var valid=false;
    var val=$(inputId)[0].value;
    var no_space=val.split(" ").join("");
    if (val!=no_space){
        $(inputId).removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg").addClass("show-error-msg");
        $(spanId).html("Este campo no debe contener espacios.");
    }
    else{
        $(inputId).removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg").addClass("error-msg");
        valid=true;
    }
    return valid;

}

function validateMail(inputId,spanId){
    var valid=false;
    var val=$(inputId)[0].value;
    var patt=/^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
    if (patt.exec(val)==null){
        $(inputId).removeClass("valid-field").addClass("invalid-field");
        $(spanId).removeClass("error-msg").addClass("show-error-msg");
        $(spanId).html("Debe ingresar una dirección de correo válida.");
    }
    else{
        $(inputId).removeClass("invalid-field").addClass("valid-field");
        $(spanId).removeClass("show-error-msg").addClass("error-msg");
        valid=true;
    }
    return valid;
}

function checkDate(from,to){
    var today=new Date().toISOString().split("T")[0];
    var split_date=today.split("-");
    split_date[2]="01";
    var first_day=split_date.join("-");
    if (from==""){
        $("#TLdateFrom").val(first_day);
        from=first_day;
        if (to==""){
            to=today;
            $("#TLdateTo").val(today);
        }
    }
    if (to==""){
        to=today;
        $("#TLdateTo").val(today);
    }
    if (from!="" && to!=""){
        var cfrom = new Date(from);
        var cto = new Date(to);
        if (cfrom>cto){
            return to,to;
        }
        if (cfrom<=cto){
            return from,to;
        }
    }
    else{
        to=today;
        from=first_day;
        return from,to;
    }

}
