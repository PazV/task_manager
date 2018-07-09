$(document).ready(function(){
    var me = this;
    this.user_info=JSON.parse($("#spnSession")[0].textContent);
    console.log("grd task")


    $("#grdTask").DataTable({
        "scrollY": "255px",
        "scrollCollapse":true,
        serverSide:true,
        ajax:{
            data:{
                'company_id':me.user_info.company_id,
                'user_id':me.user_info.user_id,
                'user_type_id':me.user_info.user_type_id,
                'filter':JSON.stringify({'a.status_id':-1})
            },
            url:'/task/getTask',
            dataSrc:'data',
            type:'POST'
        },
        columns:[
            {data:'created', "width":"15%"},
            {data:'name',"width":"20%"},
            {data:'deadline',"width":"15%"},
            {data:'assignee',"width":"20%"},
            {data:'supervisor',"width":"20%"},
            {data:'status',"width":"10%"}
        ]
    });

    $("#btnCollapseCalendar").click(function(){
        if ($("#SBcalendar").css("display")=="none"){
            $("#taskContainer").removeClass("col-lg-12").addClass("col-lg-9");
            $("#SBcalendar").css("display","block");
            $("#SBcalendar").addClass("col-lg-3");
        }
        else{
            $("#SBcalendar").css("display","none");
            $("#SBcalendar").removeClass("col-lg-3");
            $("#taskContainer").removeClass("col-lg-9").addClass("col-lg-12");

        }
        $("#grdTask").DataTable().columns.adjust().draw();
    });

    $("#TLselStatus").change(function(){
        console.log($("#TLselStatus option:selected")[0].value);
        console.log($("#TLselStatus option:selected")[0].id);

        $("#grdTask").DataTable({
            "scrollY": "255px",
            "scrollCollapse":true,
            serverSide:true,
            ajax:{
                data:{
                    'company_id':me.user_info.company_id,
                    'user_id':me.user_info.user_id,
                    'user_type_id':me.user_info.user_type_id,
                    'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                },
                url:'/task/getTask',
                dataSrc:'data',
                type:'POST'
            },
            columns:[
                {data:'created', "width":"15%"},
                {data:'name',"width":"20%"},
                {data:'deadline',"width":"15%"},
                {data:'assignee',"width":"20%"},
                {data:'supervisor',"width":"20%"},
                {data:'status',"width":"10%"}
            ]
        });

    });

    $("#btnCancelNewTask").click(function(){
        $("#win_new_task").modal("hide");
    });

    $("#win_new_task").on('hidden.bs.modal',function(){
        resetForm("#frmNewTask",["input|INPUT","select|SELECT","textarea|TEXTAREA"]);
        $("#NTselRecurrentFrequency").css("display","none");
        $("#NTchkRecurrentTask").prop("checked",false);
        $("#NTchkNotifyAdmin").prop("checked",false);
        $("#NTtask_evidences").empty();

    });

    $("#win_new_task").on('show.bs.modal',function(){
        // console.log(me.user_info)
        $.ajax({
            url:'/task/getSupervisor',
            method:'POST',
            data:JSON.stringify({
                'company_id':me.user_info['company_id'],
                'user_id':me.user_info['user_id'],
                'user_type_id':me.user_info['user_type_id']
            }),
            success:function(response){
                var res_sup=JSON.parse(response);
                if (res_sup.success){
                    $.each(res_sup.data,function(i, item){
                        $("#NTsupervisor_id").append($('<option>',{
                            text:item.name,
                            name:item.supervisor_id
                        }));
                    });
                    $.ajax({
                        url:'/task/getAssignee',
                        method:'POST',
                        data:JSON.stringify({
                            'company_id':me.user_info['company_id']
                        }),
                        success:function(responseA){
                            var res_as=JSON.parse(responseA);
                            if (res_as.success){
                                $.each(res_as.data,function(i,item){
                                    $("#NTassignee_id").append($('<option>',{
                                        text:item.name,
                                        name:item.assignee_id
                                    }));
                                });
                                $.ajax({
                                    url:'/task/getDocumentType',
                                    method:'POST',
                                    data:JSON.stringify({}),
                                    success:function(responseD){
                                        var resD=JSON.parse(responseD);
                                        if (resD.success){
                                            me.document_type_list=resD.data;
                                        }
                                    }
                                });
                            }
                        }
                    });
                }
            }
        });
        var month_list=[{'text':'1 mes','name':1},{'text':'2 meses','name':2},{'text':'3 meses','name':3},{'text':'4 meses','name':4},
        {'text':'5 meses','name':5},{'text':'6 meses','name':6},{'text':'7 meses','name':7},{'text':'8 meses','name':8},
        {'text':'9 meses','name':9},{'text':'10 meses','name':10},{'text':'11 meses','name':11},{'text':'12 meses','name':12}];
        $.each(month_list,function(i,item){
            $("#NTselRecurrentFrequency").append($('<option>',{
                text:item.text,
                name:item.name
            }));
        });
        var today=new Date().toISOString().split("T")[0];
        $("#NTdeadline").val(today);
        $("#NTsupervisor_deadline").val(today);
        $("#NTassigee_deadline").val(today);
        me.evidence_counter=1;
        me.evidence_list=[];
    });

    $("#NTname").focusout(function(){
        emptyField("#NTname","#spnNTname");
    });
    $("#NTdescription").focusout(function(){
        emptyField("#NTdescription","#spnNTdescription");
    });
    $("#NTdeadline").focusout(function(){
        var valid_empty=emptyField("#NTdeadline","#spnNTdeadline");
        // if (valid_empty){
        //     //validar que fecha de supervisor sea menor o igual a fecha límite
        // }
    });
    $("#NTsupervisor_deadline").focusout(function(){
        var valid_empty=emptyFieldRow("#NTsupervisor_deadline","#spnNTsupervisor_deadline");
        if (valid_empty){
            if ($("#NTdeadline")[0].value!=""){
                if ($("#NTsupervisor_deadline")[0].value>$("#NTdeadline")[0].value){
                    $("#NTsupervisor_deadline").removeClass("valid-field").addClass("invalid-field");
                    $("#spnNTsupervisor_deadline").removeClass("error-msg-row").addClass("show-error-msg-row");
                    $("#spnNTsupervisor_deadline").html("Fecha de supervisor debe ser menor o igual a la fecha de vencimiento");
                }
            }
        }
    });
    $("#NTassigee_deadline").focusout(function(){
        var valid_empty=emptyFieldRow("#NTassigee_deadline","#spnNTassigee_deadline");
        if (valid_empty){
            //validar que fecha de auxiliar sea menor o igual a fecha límite
            if ($("#NTsupervisor_deadline")[0].value!=""){
                if ($("#NTassigee_deadline")[0].value>$("#NTsupervisor_deadline")[0].value){
                    $("#NTassigee_deadline").removeClass("valid-field").addClass("invalid-field");
                    $("#spnNTassigee_deadline").removeClass("error-msg-row").addClass("show-error-msg-row");
                    $("#spnNTassigee_deadline").html("Fecha de auxiliar debe ser menor o igual a fecha de supervisor");
                }
            }
        }
    });

    $("#NTchkRecurrentTask").click(function(){
        if ($("#NTchkRecurrentTask")[0].checked){
            $("#NTselRecurrentFrequency").css("display","block");
        }
        else{
            $("#NTselRecurrentFrequency").css("display","none");
        }
    });

    $("#btnSaveNewTask").click(function(){
        var input_list=$("#frmNewTask").find(":input");
        var is_valid=true;
        $("#NTdeadline").focusout();
        $("#NTsupervisor_deadline").focusout();
        $("#NTassigee_deadline").focusout();
        for (x in input_list){
            if (input_list[x].type=='text' || input_list[x].type=='date' || input_list[x].type=='textarea'){
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
            var sel_list=[{'id':"#NTsupervisor_id",'name':"supervisor_id"},{'id':"#NTassignee_id",'name':"assignee_id"},{'id':"#NTselRecurrentFrequency",'name':"recurrent_frequency"}];
            var data=getDictForm("#frmNewTask",sel_list);
            data['recurrent_task']=$("#NTchkRecurrentTask")[0].checked;
            data['notify_admin']=$("#NTchkNotifyAdmin")[0].checked;
            data['company_id']=me.user_info['company_id'];
            data['user_id']=me.user_info['user_id'];
            data['document']=JSON.stringify(me.evidence_list);
            console.log(data);
            $.ajax({
                url:'/task/saveTask',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    var res=JSON.parse(response);
                    if (res.success){
                        EasyLoading.hide();
                        $("#alertLayout").find('p').html(res.msg_response);
                        $("#alertLayout").css("display","block");
                        $("#win_new_task").modal("hide");
                        $("#grdTask").DataTable({
                            "scrollY": "255px",
                            "scrollCollapse":true,
                            serverSide:true,
                            ajax:{
                                data:{
                                    'company_id':me.user_info.company_id,
                                    'user_id':me.user_info.user_id,
                                    'user_type_id':me.user_info.user_type_id,
                                    'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                },
                                url:'/task/getTask',
                                dataSrc:'data',
                                type:'POST'
                            },
                            columns:[
                                {data:'created', "width":"15%"},
                                {data:'name',"width":"20%"},
                                {data:'deadline',"width":"15%"},
                                {data:'assignee',"width":"20%"},
                                {data:'supervisor',"width":"20%"},
                                {data:'status',"width":"10%"}
                            ]
                        });
                    }
                    else{
                        EasyLoading.hide();
                        setMessage("#alertNTForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(error){
                    EasyLoading.hide();
                    setMessage("#alertNTForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                }
            });
        }
        else{
            setMessage("#alertNTForm",["alert-info","alert-success"],"alert-danger","Existen campos vacíos o incorrectos, favor de revisar.",true);
        }
    });

    $("#btnTaskDetails").click(function(){
        var table=$("#grdTask").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            data['task_id']=record['task_id'];
            data['user_id']=me.user_info.user_id;
            data['company_id']=me.user_info.company_id;
            data['user_type_id']=me.user_info.user_type_id;
            data['from']='details';
            console.log(record);
            console.log(data);
            $.ajax({
                url:'/task/getTaskDetails',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    var res=JSON.parse(response);
                    if (res.success){
                        $("#TDtask_info").html(res.data);
                        $("#win_task_details").modal("show");
                    }
                    else{
                        $.alert({
                            theme:'dark',
                            title:'Atención',
                            content:res.msg_response
                        });
                    }
                },
                error:function(){
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'Ocurrió un error al intentar obtener la información de la tarea, favor de intentarlo de nuevo.'
                    });
                }
            });
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea!'
            });
        }

    });
    $("#btnCloseTaskDetails").click(function(){
        $("#win_task_details").modal("hide");
    });


    $("#btnResolveTaskList").click(function(){
        var table=$("#grdTask").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            console.log(record);
            if (record['status_id']==1 || record['status_id']==6){
                data['task_id']=record['task_id'];
                data['user_id']=me.user_info.user_id;
                data['company_id']=me.user_info.company_id;
                data['user_type_id']=me.user_info.user_type_id;
                data['from']='resolve';
                $.ajax({
                    url:'/task/getTaskDetails',
                    method:'POST',
                    data:JSON.stringify(data),
                    success:function(response){
                        var res=JSON.parse(response);
                        if (res.success){
                            $("#RTtask_info").html(res.data);
                            if (res.html_docs.length>0){
                                for (x in res.html_docs){
                                    $("#RTfrmevidences").append(res.html_docs[x]);
                                    if (record['status_id']==6){
                                        $("#RTcomments").val(res.comments);
                                    }
                                }
                            }
                        }
                    }
                });
                $("#win_resolve_task").modal("show");
            }
            else{
                if (record['status_id']==2){
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'Esta tarea ya ha sido resuelta'
                    });
                }
                else{
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'No es posible resolver esta tarea'
                    })
                }
            }
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea!'
            });
        }

    });

    $("#RTfrmevidences").on('change','.file-evidence',function(){
        var input_id=$(this)[0].id;
        var pattern=$(this)[0].pattern.split(",");
        var span="#spn"+input_id;
        if (hasExtension(input_id,pattern) ) {
            $(this).removeClass("file-input");
            $(this).removeClass("invalid-file-field");
            $(this).addClass("valid-file-field");
            $(span).html("Error");
            $(span).removeClass("show-error-msg").addClass("error-msg");
        }
        else{
            $(this).removeClass("file-input");
            $(this).removeClass("valid-file-field");
            $(this).addClass("invalid-file-field");
            $(span).html("Formato incorrecto");
            $(span).removeClass("error-msg").addClass("show-error-msg");
        }
    });


    $("#btnCloseResolveTask").click(function(){
        $("#win_resolve_task").modal("hide");
    });

    $("#win_resolve_task").on('hidden.bs.modal',function(){
        $("#RTcomments").val([]);
        $("#RTfrmevidences").empty();
    });

    $("#btnResolveTask").click(function(){
        var frm_evidence=$("#RTfrmevidences").find("input");
        var is_valid=true;
        for (y in frm_evidence){
            if (frm_evidence[y].type=='file'){
                if ($("#"+frm_evidence[y].id).hasClass("valid-file-field")===false){
                    is_valid=false;
                }
            }
        }
        if (is_valid){
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            });
            var total_size=0;
            var total_size_MB=0;
            for (x in frm_evidence){
                if (frm_evidence[x].type=='file'){
                    try{
                        console.log(frm_evidence[x].files[0].size);
                        total_size+=frm_evidence[x].files[0].size;
                    }
                    catch(err){
                        total_size+=parseFloat($("#"+frm_evidence[x].id).data('size'))*1048576;
                    }
                }
            }
            console.log(total_size);
            console.log(total_size/1024 +"KB");
            total_size_MB=total_size/1024/1024;
            console.log(total_size_MB +"MB");
            if (total_size_MB<=3){
                var files_list=[];
                var frm=new FormData();
                for (i in frm_evidence){
                    if (frm_evidence[i].type=='file'){
                        try{
                            frm_evidence[i].files[0].size;
                            name=frm_evidence[i].name;
                            file=frm_evidence[i].files[0];
                            files_list.push(name);
                            frm.append(name,file);
                        }
                        catch(err){
                            console.log(err);
                        }
                    }
                }
                console.log(files_list);
                //lega en files
                var table=$("#grdTask").DataTable();
                var ind=table.row('.selected').index();
                var record=table.rows(ind).data()[0];
                frm.append('task_id',record['task_id']);
                frm.append('user_id',me.user_info.user_id);
                frm.append('company_id',me.user_info.company_id);
                frm.append('user_type_id',me.user_info.user_type_id);
                frm.append('files_list',JSON.stringify(files_list));
                frm.append('comments',$("#RTcomments")[0].value);
                frm.append('status_id',record['status_id']);

                //frm.append('task_id','1'); //llega en form
                $.ajax({
                    url:'/task/resolveTask',
                    data:frm,
                    type:'POST',
                    processData: false,
                    contentType: false,
                    success:function(response){
                        var res=JSON.parse(response);
                        if (res.success){
                            EasyLoading.hide();
                            $("#alertLayout").find('p').html(res.msg_response);
                            $("#alertLayout").css("display","block");
                            $("#win_resolve_task").modal("hide");
                            $("#grdTask").DataTable({
                                "scrollY": "255px",
                                "scrollCollapse":true,
                                serverSide:true,
                                ajax:{
                                    data:{
                                        'company_id':me.user_info.company_id,
                                        'user_id':me.user_info.user_id,
                                        'user_type_id':me.user_info.user_type_id,
                                        'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                    },
                                    url:'/task/getTask',
                                    dataSrc:'data',
                                    type:'POST'
                                },
                                columns:[
                                    {data:'created', "width":"15%"},
                                    {data:'name',"width":"20%"},
                                    {data:'deadline',"width":"15%"},
                                    {data:'assignee',"width":"20%"},
                                    {data:'supervisor',"width":"20%"},
                                    {data:'status',"width":"10%"}
                                ]
                            });
                        }
                        else{
                            EasyLoading.hide();
                            setMessage("#alertRTForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                        }

                    },
                    error:function(){
                        EasyLoading.hide();
                        setMessage("#alertRTForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                    }
                });
            }
            else{
                EasyLoading.hide();
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'La suma de todas las evidencias no puede ser mayor a 3 MB, en este momento tienes '+total_size_MB.toFixed(3)+' MB. Comprime tus archivos e inténtalo de nuevo.'
                });
            }
        }
        else{
            setMessage("#alertRTForm",["alert-info","alert-success"],"alert-danger","Existen campos vacíos o incorrectos, favor de revisar.",true);

        }
    });

    $("#btnPauseResolveTask").click(function(){
        var total_file_fields=$("#RTfrmevidences").find("input").length;
        var input_list=$("#RTfrmevidences").find("input");
        var is_valid=true;
        var count_valid=0;
        for (y in input_list){
            if (input_list[y].type=='file'){
                if ($("#"+input_list[y].id).hasClass("valid-file-field")){
                    count_valid+=1;
                }
            }
        }
        var comments=$("#RTcomments")[0].value;
        if (comments!="" || count_valid>0){
            //guardar datos
            var data=new FormData();
            var files_list=[];
            var total_size=0;
            var total_size_MB=0;
            for (x in input_list){
                if (input_list[x].type=='file'){ //verificar si es de tipo file
                    if ($("#"+input_list[x].id).hasClass("valid-file-field")){
                        if (input_list[x].files.length>0){ //verificar si tiene un archivo cargado
                            name=input_list[x].name;
                            file=input_list[x].files[0];
                            files_list.push(name);
                            data.append(name,file);
                            total_size+=input_list[x].files[0].size;
                            console.log(input_list[x].files[0].size);
                        }
                        else{
                            total_size+=parseFloat($("#"+input_list[x].id).data('size'))*1048576;
                            console.log(parseFloat($("#"+input_list[x].id).data('size'))*1048576);
                        }
                    }
                }
            }
            total_size_MB=total_size/1024/1024;
            if (total_size_MB<=3){
                var table=$("#grdTask").DataTable();
                var ind=table.row('.selected').index();
                var record=table.rows(ind).data()[0];
                console.log(record);
                data.append('task_id',record['task_id']);
                data.append('user_id',me.user_info.user_id);
                data.append('company_id',me.user_info.company_id);
                data.append('user_type_id',me.user_info.user_type_id);
                data.append('status_id',record['status_id']);
                data.append('comments',$("#RTcomments")[0].value);
                data.append('files_list',JSON.stringify(files_list));
                EasyLoading.show({
                    text:"Cargando...",
                    type:EasyLoading.TYPE["PACMAN"]
                });
                $.ajax({
                    url:'/task/pauseResolveTask',
                    type:'POST',
                    data:data,
                    processData: false,
                    contentType: false,
                    success:function(response){
                        var res=JSON.parse(response);
                        EasyLoading.hide();
                        if (res.success){
                            $("#alertLayout").find('p').html(res.msg_response);
                            $("#alertLayout").css("display","block");
                            $("#win_resolve_task").modal("hide");
                            $("#grdTask").DataTable({
                                "scrollY": "255px",
                                "scrollCollapse":true,
                                serverSide:true,
                                ajax:{
                                    data:{
                                        'company_id':me.user_info.company_id,
                                        'user_id':me.user_info.user_id,
                                        'user_type_id':me.user_info.user_type_id,
                                        'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                    },
                                    url:'/task/getTask',
                                    dataSrc:'data',
                                    type:'POST'
                                },
                                columns:[
                                    {data:'created', "width":"15%"},
                                    {data:'name',"width":"20%"},
                                    {data:'deadline',"width":"15%"},
                                    {data:'assignee',"width":"20%"},
                                    {data:'supervisor',"width":"20%"},
                                    {data:'status',"width":"10%"}
                                ]
                            });
                        }
                        else{
                            EasyLoading.hide();
                            setMessage("#alertRTForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                        }
                    },
                    error:function(){
                        EasyLoading.hide();
                        setMessage("#alertRTForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                    }
                });
            }
            else{
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'La suma de todas las evidencias no puede ser mayor a 3 MB, en este momento tienes '+total_size_MB.toFixed(3)+' MB. Comprime tus archivos e inténtalo de nuevo.'
                });
            }
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'Debe agregar comentarios y/o al menos una evidencia para poder guardar los cambios hasta este punto.'
            });
        }
    });

    $("#btnDeclineTaskList").click(function(){
        var table=$("#grdTask").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            if (record['status_id']==1){
                data['task_id']=record['task_id'];
                data['user_id']=me.user_info.user_id;
                data['company_id']=me.user_info.company_id;
                data['user_type_id']=me.user_info.user_type_id;
                data['from']='decline';
                $.ajax({
                    url:'/task/getTaskDetails',
                    method:'POST',
                    data:JSON.stringify(data),
                    success:function(response){
                        var res=JSON.parse(response);
                        if (res.success){
                            $("#DecTinfo").html(res.data);
                        }
                    }
                });
                $("#win_decline_task").modal("show");
            }
            else{
                if (record['status_id']==2){
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'Esta tarea ya ha sido resuelta'
                    });
                }
                else{
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'No es posible declinar esta tarea'
                    })
                }
            }
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea!'
            });
        }
    });

    $("#DecTcomments").focusout(function(){
        emptyField("#DecTcomments","#spnDecTdescription");
    });

    $("#btn").click(function(){
        EasyLoading.show({
            text:"Cargando...",
            type:EasyLoading.TYPE["PACMAN"],
            timeout:2000
        });
    })

    $("#btnDeclineTask").click(function(){
        var is_valid=true;
        $("#DecTcomments").focusout();
        if ($("#DecTcomments").hasClass('valid-field')===false){
            is_valid=false;
        }
        if (is_valid){
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            });
            var table=$("#grdTask").DataTable();
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            data['task_id']=record['task_id'];
            data['user_id']=me.user_info.user_id;
            data['company_id']=me.user_info.company_id;
            data['comments']=$("#DecTcomments")[0].value;
            $.ajax({
                url:'/task/declineTask',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    var res=JSON.parse(response);
                    if (res.success){
                        EasyLoading.hide();
                        $("#alertLayout").find('p').html(res.msg_response);
                        $("#alertLayout").css("display","block");
                        $("#win_resolve_task").modal("hide");
                        $("#grdTask").DataTable({
                            "scrollY": "255px",
                            "scrollCollapse":true,
                            serverSide:true,
                            ajax:{
                                data:{
                                    'company_id':me.user_info.company_id,
                                    'user_id':me.user_info.user_id,
                                    'user_type_id':me.user_info.user_type_id,
                                    'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                },
                                url:'/task/getTask',
                                dataSrc:'data',
                                type:'POST'
                            },
                            columns:[
                                {data:'created', "width":"15%"},
                                {data:'name',"width":"20%"},
                                {data:'deadline',"width":"15%"},
                                {data:'assignee',"width":"20%"},
                                {data:'supervisor',"width":"20%"},
                                {data:'status',"width":"10%"}
                            ]
                        });
                        $("#win_decline_task").modal("hide");
                    }
                    else{
                        EasyLoading.hide();
                        setMessage("#alertDecTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(){
                    EasyLoading.hide();
                    setMessage("#alertDecTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                }
            });
        }
    });

    $("#btnCloseDeclineTask").click(function(){
        $("#win_decline_task").modal("hide");
    });

    $("#win_decline_task").on('hidden.bs.modal',function(){
        $("#DecTcomments").val([]);
        $("#DecTcomments").removeClass("valid-field");
        $("#DecTcomments").removeClass("invalid-field");
        $("#spnDecTdescription").removeClass("show-error-msg");
        $("#spnDecTdescription").addClass("error-msg");
        $("#spnDecTdescription").html("Error");
    })

    $("#btnAddEvidence").click(function(){
        $("#win_add_evidence").modal("show");
    });

    $("#win_add_evidence").on('show.bs.modal',function(){

        $.each(me.document_type_list,function(i,item){
            $("#TEdocument_type").append($('<option>',{
                text:item.document_type,
                name:item.document_type_id
            }));
        });
    });

    $("#NTtask_evidences").on('click','.close-evidence-container',function(){
        var div_id=$(this).parent('div')[0].id;
        $(this).parent('div').remove();
        var list_to_eliminate=jQuery.extend({}, me.evidence_list);
        for (x in list_to_eliminate){
            if (list_to_eliminate[x].id==div_id){
                var ind=me.evidence_list.indexOf(list_to_eliminate[x]);
                me.evidence_list.splice(ind,1);
            }
        }
    });

    $("#TEname").focusout(function(){
        var val_empty=emptyFieldRow("#TEname","#spnTEname");
        if (val_empty){
            maxLenRow("#TEname","#spnTEname",45);
        }
    });

    $("#TEdescription").focusout(function(){
        emptyField("#TEdescription","#spnTEdescription");
    });

    $("#btnSaveEvidence").click(function(){
        var input_list=$("#frmAddEvidence").find(":input");
        var is_valid=true;
        $("#TEname").focusout();
        $("#TEdescription").focusout();
        for (x in input_list){
            if (input_list[x].type=='text' || input_list[x].type=='textarea'){
                if ($("#"+input_list[x].id).hasClass('valid-field')===false){
                    $("#"+input_list[x].id).focusout();
                    console.log(input_list[x].id);
                    is_valid=false;
                }
            }
        }
        if (is_valid){
            var sel_list=[{'id':"#TEdocument_type",'name':"document_type_id"}];
            var data=getDictForm("#frmAddEvidence",sel_list);
            console.log(data);
            data['id']=me.evidence_counter;
            me.evidence_list.push(data);
            var div='<div class="evidence-container" id="'+data['id']+'">'+data['name']+' - ('+data['document_type']+')<a class="close-evidence-container pull-right" data-toggle="tooltip" title="Eliminar evidencia"><i class="fa fa-times"></i></a></div>'
            $("#NTtask_evidences").append(div);
            $("#win_add_evidence").modal("hide");
            me.evidence_counter+=1;
        }
        else{
            setMessage("#alertTEForm",["alert-info","alert-success"],"alert-danger","Existen campos vacíos o incorrectos, favor de revisar.",true);
        }
    });

    $("#win_add_evidence").on('hidden.bs.modal',function(){
        resetForm("#frmAddEvidence",["input|INPUT","select|SELECT","textarea|TEXTAREA"]);
    });



    $("#btnCloseAddEvidence").click(function(){
        $("#win_add_evidence").modal("hide");
    });

    $("#btnCheckTaskList").click(function(){
        var table=$("#grdTask").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            if (record['status_id']==2 || record['status_id']==3){
                data['task_id']=record['task_id'];
                data['user_id']=me.user_info.user_id;
                data['company_id']=me.user_info.company_id;
                data['user_type_id']=me.user_info.user_type_id;
                if (record['status_id']==2){
                    data['from']='check';
                    $.ajax({
                        url:'/task/getTaskDetails',
                        method:'POST',
                        data:JSON.stringify(data),
                        success:function(response){
                            var res=JSON.parse(response);
                            if (res.success){
                                $("#CHTtask_info").html(res.data);
                                $("#CHTevidences").append(res.evidence);
                            }
                        }
                    });
                    $("#win_check_task").modal("show");
                }
                else{
                    data['from']='check_declined';
                    $.ajax({
                        url:'/task/getTaskDetails',
                        method:'POST',
                        data:JSON.stringify(data),
                        success:function(response){
                            var res=JSON.parse(response);
                            if (res.success){
                                $("#CHDTtask_info").html(res.data);
                                $.ajax({
                                    url:'/task/getAssignee',
                                    method:'POST',
                                    data:JSON.stringify({'company_id':me.user_info.company_id}),
                                    success:function(assignee_response){
                                        var assig_res=JSON.parse(assignee_response);
                                        if (assig_res.success){
                                            var items=assig_res.data;
                                            $.each(items,function(i, item){
                                                if (item.assignee_id==record['assignee_id']){
                                                    $("#CHDTassignee_id").append($('<option>',{
                                                        text:item.name,
                                                        name:item.assignee_id,
                                                        selected:true
                                                    }));
                                                }
                                                else{
                                                    $("#CHDTassignee_id").append($('<option>',{
                                                        text:item.name,
                                                        name:item.assignee_id,
                                                        selected:false
                                                    }));
                                                }
                                            });
                                            $("#CHDTdescription").html(record['description']);
                                        }
                                    }
                                })
                            }
                        }
                    });
                    $("#win_check_declined_task").modal("show");
                }
            }
            else{
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'Esta tarea no puede ser revisada'
                });
            }
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'Debe seleccionar una tarea para revisarla'
            });
        }
    });

    $("#btnCheckTaskComplete").click(function(){
        $.confirm({
            theme:'dark',
            title: 'Atención',
            content: 'Al confirmar que la tarea está correcta, ésta será cerrada, ¿desea continuar?',
            buttons: {
                confirm:{
                    text:'Sí',
                    action: function () {
                        EasyLoading.show({
                            text:"Cargando...",
                            type:EasyLoading.TYPE["PACMAN"],
                        });
                        var table=$("#grdTask").DataTable();
                        var ind=table.row('.selected').index();
                        var record=table.rows(ind).data()[0];
                        var data={};
                        data['task_id']=record['task_id'];
                        data['company_id']=record['company_id'];
                        data['user_id']=me.user_info.user_id;
                        data['comments']=$("#CHTcomments")[0].value;
                        $.ajax({
                            url:'/task/completeTask',
                            method:'POST',
                            data:JSON.stringify(data),
                            success:function(response){
                                var res=JSON.parse(response);
                                if (res.success){
                                    EasyLoading.hide();
                                    $("#alertLayout").find('p').html(res.msg_response);
                                    $("#alertLayout").css("display","block");
                                    $("#win_check_task").modal("hide");
                                    $("#grdTask").DataTable({
                                        "scrollY": "255px",
                                        "scrollCollapse":true,
                                        serverSide:true,
                                        ajax:{
                                            data:{
                                                'company_id':me.user_info.company_id,
                                                'user_id':me.user_info.user_id,
                                                'user_type_id':me.user_info.user_type_id,
                                                'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                            },
                                            url:'/task/getTask',
                                            dataSrc:'data',
                                            type:'POST'
                                        },
                                        columns:[
                                            {data:'created', "width":"15%"},
                                            {data:'name',"width":"20%"},
                                            {data:'deadline',"width":"15%"},
                                            {data:'assignee',"width":"20%"},
                                            {data:'supervisor',"width":"20%"},
                                            {data:'status',"width":"10%"}
                                        ]
                                    });
                                }
                                else{
                                    EasyLoading.hide();
                                    setMessage("#alertCHTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                                }
                            },
                            error:function(){
                                EasyLoading.hide();
                                setMessage("#alertCHTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                            }
                        });
                    }
                },
                cancel:{
                    text:'No'
                }
            }
        });

    });

    $("#btnCheckTaskIncomplete").click(function(){
        $.confirm({
            theme:'dark',
            title:'Atención',
            content:'Al marcar la tarea como incompleta, cambiará su estado a Pendiente y será asignada nuevamente al auxiliar, ¿desea continuar?',
            buttons:{
                confirm:{
                    text:'Sí',
                    action:function(){
                        EasyLoading.show({
                            text:"Cargando...",
                            type:EasyLoading.TYPE["PACMAN"],
                        });
                        var data={};
                        var table=$("#grdTask").DataTable();
                        var ind=table.row('.selected').index();
                        var record=table.rows(ind).data()[0];
                        data['task_id']=record['task_id'];
                        data['company_id']=record['company_id'];
                        data['user_id']=me.user_info.user_id;
                        data['comments']=$("#CHTcomments")[0].value;
                        $.ajax({
                            url:'/task/incompleteTask',
                            method:'POST',
                            data:JSON.stringify(data),
                            success:function(response){
                                var res=JSON.parse(response);
                                if (res.success){
                                    EasyLoading.hide();
                                    $("#alertLayout").find('p').html(res.msg_response);
                                    $("#alertLayout").css("display","block");
                                    $("#win_check_task").modal("hide");
                                    $("#grdTask").DataTable({
                                        "scrollY": "255px",
                                        "scrollCollapse":true,
                                        serverSide:true,
                                        ajax:{
                                            data:{
                                                'company_id':me.user_info.company_id,
                                                'user_id':me.user_info.user_id,
                                                'user_type_id':me.user_info.user_type_id,
                                                'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                            },
                                            url:'/task/getTask',
                                            dataSrc:'data',
                                            type:'POST'
                                        },
                                        columns:[
                                            {data:'created', "width":"15%"},
                                            {data:'name',"width":"20%"},
                                            {data:'deadline',"width":"15%"},
                                            {data:'assignee',"width":"20%"},
                                            {data:'supervisor',"width":"20%"},
                                            {data:'status',"width":"10%"}
                                        ]
                                    });
                                }
                                else{
                                    EasyLoading.hide();
                                    setMessage("#alertCHTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                                }
                            },
                            error:function(){
                                EasyLoading.hide();
                                setMessage("#alertCHTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error al intentar enviar la información, favor de intentarlo de nuevo.",true);
                            }
                        });
                    }
                },
                cancel:{
                    text:'No'
                }
            }
        });
    });

    $("#win_check_task").on('hidden.bs.modal',function(){
        $("#CHTcomments").val([]);
        $("#CHTevidences").empty();
    });

    $("#btnCloseCheckTask").click(function(){
        $("#win_check_task").modal("hide");
    });

    $("#btnCloseCheckDeclinedTask").click(function(){
        $("#win_check_declined_task").modal("hide");
    });

    $("#win_check_declined_task").on('hidden.bs.modal',function(){
        resetForm("#frmCheckDeclinedTask",['textarea|TEXTAREA','select|SELECT']);
    });

    $("#btnSaveCheckDeclinedTask").click(function(){
        var sel_list=[{'id':"#CHDTassignee_id",'name':"assignee_id"}];
        var data=getDictForm("#frmCheckDeclinedTask",sel_list);
        var table=$("#grdTask").DataTable();
        var ind=table.row('.selected').index();
        var record=table.rows(ind).data()[0];
        data['task_id']=record['task_id'];
        data['user_id']=me.user_info.user_id;
        if (data['description']==""){
            $.confirm({
                theme:'dark',
                title:'Atención',
                content:'Se guardará la tarea con la descripción anterior, ¿desea continuar?',
                buttons:{
                    confirm:{
                        text:'Sí',
                        action:function(){
                            EasyLoading.show({
                                text:"Cargando...",
                                type:EasyLoading.TYPE["PACMAN"],
                            });
                            $.ajax({
                                url:'/task/updateDeclinedTask',
                                method:'POST',
                                data:JSON.stringify(data),
                                success:function(response){
                                    var res=JSON.parse(response);
                                    if (res.success){
                                        EasyLoading.hide();
                                        $("#alertLayout").find('p').html(res.msg_response);
                                        $("#alertLayout").css("display","block");
                                        $("#win_check_declined_task").modal("hide");
                                        $("#grdTask").DataTable({
                                            "scrollY": "255px",
                                            "scrollCollapse":true,
                                            serverSide:true,
                                            ajax:{
                                                data:{
                                                    'company_id':me.user_info.company_id,
                                                    'user_id':me.user_info.user_id,
                                                    'user_type_id':me.user_info.user_type_id,
                                                    'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                                },
                                                url:'/task/getTask',
                                                dataSrc:'data',
                                                type:'POST'
                                            },
                                            columns:[
                                                {data:'created', "width":"15%"},
                                                {data:'name',"width":"20%"},
                                                {data:'deadline',"width":"15%"},
                                                {data:'assignee',"width":"20%"},
                                                {data:'supervisor',"width":"20%"},
                                                {data:'status',"width":"10%"}
                                            ]
                                        });
                                    }
                                    else{
                                        EasyLoading.hide();
                                        setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                                    }
                                },
                                error:function(){
                                    EasyLoading.hide();
                                    setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
                                }
                            });
                        }
                    },
                    cancel:{
                        text:'No'
                    }
                }

            })
        }
        else{
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            });
            $.ajax({
                url:'/task/updateDeclinedTask',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    var res=JSON.parse(response);
                    if (res.success){
                        EasyLoading.hide();
                        $("#alertLayout").find('p').html(res.msg_response);
                        $("#alertLayout").css("display","block");
                        $("#win_check_declined_task").modal("hide");
                        $("#grdTask").DataTable({
                            "scrollY": "255px",
                            "scrollCollapse":true,
                            serverSide:true,
                            ajax:{
                                data:{
                                    'company_id':me.user_info.company_id,
                                    'user_id':me.user_info.user_id,
                                    'user_type_id':me.user_info.user_type_id,
                                    'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                },
                                url:'/task/getTask',
                                dataSrc:'data',
                                type:'POST'
                            },
                            columns:[
                                {data:'created', "width":"15%"},
                                {data:'name',"width":"20%"},
                                {data:'deadline',"width":"15%"},
                                {data:'assignee',"width":"20%"},
                                {data:'supervisor',"width":"20%"},
                                {data:'status',"width":"10%"}
                            ]
                        });
                    }
                    else{
                        EasyLoading.hide();
                        setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                    }
                },
                error:function(){
                    EasyLoading.hide();
                    setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
                }
            });
        }
    });

    $("#btnCancelDeclinedTask").click(function(){
        $.confirm({
            theme:'dark',
            title:'Atención',
            content:'¿Está seguro que desea cancelar esta tarea?',
            buttons:{
                confirm:{
                    text:'Sí',
                    action:function(){
                        EasyLoading.show({
                            text:"Cargando...",
                            type:EasyLoading.TYPE["PACMAN"]
                        });
                        var table=$("#grdTask").DataTable();
                        var ind=table.row('.selected').index();
                        var record=table.rows(ind).data()[0];
                        $.ajax({
                            url:'/task/cancelTask',
                            method:'POST',
                            data:JSON.stringify({'task_id':record['task_id'],'user_id':me.user_info.user_id}),
                            success:function(response){
                                var res=JSON.parse(response);
                                EasyLoading.hide();
                                if (res.success){
                                    $("#alertLayout").find('p').html(res.msg_response);
                                    $("#alertLayout").css("display","block");
                                    $("#win_check_declined_task").modal("hide");
                                    $("#grdTask").DataTable({
                                        "scrollY": "255px",
                                        "scrollCollapse":true,
                                        serverSide:true,
                                        ajax:{
                                            data:{
                                                'company_id':me.user_info.company_id,
                                                'user_id':me.user_info.user_id,
                                                'user_type_id':me.user_info.user_type_id,
                                                'filter':JSON.stringify({'a.status_id':parseInt($("#TLselStatus option:selected")[0].id)})
                                            },
                                            url:'/task/getTask',
                                            dataSrc:'data',
                                            type:'POST'
                                        },
                                        columns:[
                                            {data:'created', "width":"15%"},
                                            {data:'name',"width":"20%"},
                                            {data:'deadline',"width":"15%"},
                                            {data:'assignee',"width":"20%"},
                                            {data:'supervisor',"width":"20%"},
                                            {data:'status',"width":"10%"}
                                        ]
                                    });
                                }
                                else{
                                    setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                                }
                            },
                            error:function(){
                                EasyLoading.hide();
                                setMessage("#alertCHDTask",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
                            }
                        });
                    }
                },
                cancel:{
                    text:'No'
                }
            }
        });
    });

});



// 
// function emptyFieldRow(fieldId,spanId){
//     var valid=false;
//     var input=$(fieldId);
//     var is_name=input.val();
//     if(is_name && (input[0].value.trim()).length>0){ //valida si es diferente de vacio y verifica que no tenga puros espacios vacios
//         input.removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg-row").addClass("error-msg-row");
//         $(spanId).html("Error");
//         valid=true;
//     }
//     else{
//         input.removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg-row").addClass("show-error-msg-row");
//         $(spanId).html("Este campo es requerido.");
//     }
//     return valid;
// }
//
// function hasExtension(inputID, exts) {
//     var fileName = document.getElementById(inputID).value;
//     return (new RegExp('(' + exts.join('|').replace(/\./g, '\\.') + ')$')).test(fileName);
// }
//
// function maxLenRow(inputId,spanId,len){
//     var valid=false;
//     var val=$(inputId)[0].value;
//     if (val.length>len){
//         $(inputId).removeClass("valid-field").addClass("invalid-field");
//         $(spanId).removeClass("error-msg-row").addClass("show-error-msg-row");
//         $(spanId).html("Este campo puede tener un máximo de "+len+" caracteres.");
//     }
//     else{
//         $(inputId).removeClass("invalid-field").addClass("valid-field");
//         $(spanId).removeClass("show-error-msg-row").addClass("error-msg-row");
//         valid=true;
//     }
//     return valid;
// }
