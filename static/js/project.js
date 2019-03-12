$(document).ready(function(){
    this.user_info=JSON.parse($("#spnSession")[0].textContent);
    var me = this;
    var today = new Date().toISOString().split("T")[0];
    var split_date = today.split("-");
    split_date[2] = "01";
    var first_day = split_date.join("-");
    $("#PLdateFrom").val(first_day);
    $("#PLdateTo").val(today);

    collapseProjectFilters();

    var show_task_view=$("#projectContainer").is(":visible");
    if (show_task_view===true){
        $("#btnChangeTaskView").css("display","block");
        $("#btnChangeProjectView").css("display","none");
    }
    else{
        $("#btnChangeTaskView").css("display","none");
        $("#btnChangeProjectView").css("display","block");
    }

    $("#win_new_project").on('show.bs.modal',function(){
        if ($("#btnEditProject").data('clicked')){
            var project_table=$("#grdProjects").DataTable();
            var project_ind=project_table.row('.selected').index();
            var project_record=project_table.rows(project_ind).data()[0];
            $("#win_new_project").data('project_id',project_record['project_id']);
            console.log("true");
        }
        else{
            $("#NPdeadline").val(today);
            $("#win_new_project").data('project_id',-1);
            console.log("false");
        }
    });

    $("#btnSaveNewProject").click(function(){
        $("#txtNPname").focusout();
        $("#NPdescription").focusout();
        $("#NPdeadline").focusout();
        var data = getDictForm("#frmNewProject",[]);
        if ($("#txtNPname").hasClass('valid-field')===false || $("#NPdeadline").hasClass('valid-field')===false){
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'Existen campos vacíos o incorrectos. Favor de verificar.'
            });
        }
        else{
            var deadline=data['deadline']+' 23:59:59';
            if ($("#win_new_project").data('project_id')!=-1){
                EasyLoading.show({
                    text:'Cargando...',
                    type:EasyLoading.TYPE["PACMAN"]
                });
                data['user_id'] = me.user_info.user_id;
                data['company_id'] = me.user_info.company_id;
                data['new_project_id']=$("#win_new_project").data('project_id');
                $.ajax({
                    url:'/project/saveProject',
                    method:'POST',
                    data:JSON.stringify(data),
                    success:function(response){
                        EasyLoading.hide();
                        try{
                            var res = JSON.parse(response);
                        }catch(err){
                            handleAjaxErrorLoc(1,2,3);
                        }
                        if (res.success){
                            $("#win_new_project").modal("hide");
                            if (res.new===true){
                                $.confirm({
                                    theme:'dark',
                                    title:'Atención',
                                    content:'Proyecto guardado exitosamente. ¿Desea agregar tareas al proyecto en este momento?',
                                    buttons:{
                                        confirm:{
                                            text:'Sí',
                                            action:function(){
                                                $.ajax({
                                                    url:'/project/getProjectInfo',
                                                    method:'POST',
                                                    data:JSON.stringify({'project_id':res.project_id}),
                                                    success:function(response_proj_info){
                                                        try{
                                                            var resp_proj_info=JSON.parse(response_proj_info);
                                                        }catch(err){
                                                            handleAjaxErrorLoc(1,2,3);
                                                        }
                                                        if (resp_proj_info.success){

                                                            $("#PrDproject_info").html(resp_proj_info.html);
                                                            $("#win_project_detail").modal("show");
                                                            $("#win_project_detail").data('project_id',res.project_id);
                                                            getProjectTasks(me.user_info,res.project_id);
                                                            setTimeout(function(){
                                                                $("#grdProjectTasks").DataTable().draw();
                                                            },200);
                                                        }
                                                        else{
                                                            $.alert({
                                                                theme:'dark',
                                                                title:'Atención',
                                                                content:resp_proj_info.msg_response
                                                            });
                                                        }
                                                    },
                                                    error:function(){
                                                        $.alert({
                                                            theme:'dark',
                                                            title:'Atención',
                                                            content:'Ocurrió un error, favor de intentarlo de nuevo.'
                                                        });
                                                    }
                                                });
                                            }
                                        },
                                        cancel:{
                                            text:'Más tarde',
                                            action:function(){
                                                //No hace nada

                                            }
                                        }
                                    }
                                });
                            }
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
                            content:'Ocurrió un error, favor de intentarlo de nuevo más tarde.'
                        });
                    }
                });
            }
            else{
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'La fecha seleccionada no es válida. Favor de verificarla.'
                });
            }
        }
    });

    $("#txtNPname").focusout(function(){
        var valid_empty_name = emptyField("#txtNPname","#spntxtNPname");
    });

    $("#NPdeadline").focusout(function(){
        var valid_empty_deadline = emptyField("#NPdeadline","#spnNPdeadline");
    });

    $("#btnCancelNewProject").click(function(){
        $("#win_new_project").modal("hide");
    });

    $("#win_new_project").on('hidden.bs.modal',function(){
        resetForm("#frmNewProject",["input|INPUT","textarea|TEXTAREA","date|DATE"]);
        setMessage("#alertNProjForm",["alert-success","alert-danger"],"alert-info","",false);
        $("#btnEditProject").data('clicked',false);
        getProjectGrd(me.user_info);
    });

    $("#btnCloseProjectDetail").click(function(){
        $("#win_project_detail").modal("hide");
    });

    $("#btnPrAddTask").click(function(){
        $.confirm({
            theme:'dark',
            title:'Atención',
            content:'¿Desea crear una tarea nueva o buscar una ya existente?',
            buttons:{
                confirm:{
                    text:'Crear nueva',
                    action:function(){
                        $("#win_new_task").modal("show");
                    }
                },
                cancel:{
                    text:'Buscar tarea',
                    action:function(){
                        $("#win_search_project_task").modal("show");
                    }
                },
                other:{
                    text:'Salir'
                }
            }
        })
    });

    $("#btnCloseSearchTask").click(function(){
        $("#win_search_project_task").modal("hide");
    });



    $.ajax({
        url:'/project/getCreatedBy',
        method:'POST',
        data:JSON.stringify({
            'company_id':me.user_info['company_id']
        }),
        success:function(response){
            try{
                var res=JSON.parse(response);
            }catch(err){
                handleAjaxErrorLoc(1,2,3);
            }
            if (res.success){
                $.each(res.data,function(i,item){
                    if (me.user_info['user_id']==item.user_id){
                        $("#PLcreatedBy").append($('<option>',{
                            text:item.name,
                            name:item.user_id,
                            selected:true
                        }));
                    }
                    else{
                        $("#PLcreatedBy").append($('<option>',{
                            text:item.name,
                            name:item.user_id
                        }));
                    }
                });
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
                content:'Ocurrió un error al intentar cargar los usuario, favor de cargar la página nuevamente.'
            });
        }
    })

    $("#grdProjects").DataTable({
        "scrollY":"225px",
        "scrollCollapse":true,
        "lengthChange":false,
        serverSide:true,
        ajax:{
            data:{
                'company_id':me.user_info.company_id,
                'user_id':me.user_info.user_id,
                'user_type_id':me.user_info.user_type_id,
                'first':true,
                'filter':JSON.stringify({
                    'status_id':1,
                    'date_type':2,
                    'from':-1,
                    'to':-1,
                    'created_by':-1,
                    'search':-1
                })
            },
            url:'/project/getProjects',
            dataSrc:'data',
            type:'POST',
            error:handleAjaxErrorLoc
        },
        columns:[
            {data:'name',"width":"20%"},
            {data:'created_by',"width":"20%"},
            {data:'created',"width":"15%"},
            {data:'deadline',"width":"15%"},
            {data:'tasks',"width":"15%"},
            {data:'status',"width":"15%"}
        ]
    });

    $("#grdProjects").on('init.dt', function(a,b,c){
        if (c.first==true){
            if (c.date_from!==false){
                $("#PLdateFrom").val(c.date_from);
                $("#PLdateTo").val(c.date_to);
            }
        }
    });

    $("#PLcreatedBy").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#PLdateType").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#PLdateFrom").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#PLdateTo").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#PLstatus").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#PLcreatedBy").change(function(){
        getProjectGrd(me.user_info);
    });

    $("#btnProjectSearch").click(function(){
        getProjectGrd(me.user_info);
    });

    $("#btnClearProjectSearch").click(function(){
        $("#PLdateFrom").val(first_day);
        $("#PLdateTo").val(today);
        $("#PLdateType option[id=2]").prop("selected",true);
        $("#PLcreatedBy option[name="+me.user_info.user_id+"]").prop("selected",true);
        $("#PLstatus option[id=-1]").prop("selected",true);
        $("#PLsearchName").val("");
        getProjectGrd(me.user_info);
    });

    $("#btnProjectDetails").click(function(){
        var table=$("#grdProjects").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            $("#win_project_detail").data('project_id',record['project_id']);
            $.ajax({
                url:'/project/getProjectInfo',
                method:'POST',
                data:JSON.stringify({'project_id':record.project_id}),
                success:function(response_proj_info){
                    try{
                        var resp_proj_info=JSON.parse(response_proj_info);
                    }catch(err){
                        handleAjaxErrorLoc(1,2,3);
                    }
                    if (resp_proj_info.success){
                        $("#PrDproject_info").html(resp_proj_info.html);
                        getProjectTasks(me.user_info,record.project_id);
                        setTimeout(function(){
                            $("#grdProjectTasks").DataTable().draw();
                        },200);
                        $("#win_project_detail").modal("show");
                    }
                    else{
                        $.alert({
                            theme:'dark',
                            title:'Atención',
                            content:resp_proj_info.msg_response
                        });
                    }
                },
                error:function(){
                    $.alert({
                        theme:'dark',
                        title:'Atención',
                        content:'Ocurrió un error, favor de intentarlo de nuevo.'
                    });
                }
            });
        }else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'Debe seleccionar un proyecto para ver sus detalles.'
            });
        }
    });


    $("#win_search_project_task").on('show.bs.modal',function(){
        $("#SPTdateFrom").val(first_day);
        $("#SPTdateTo").val(today);
        $("#SPTstatus option[id=1]").prop("selected",true);
        $("#SPTdateType option[id=2]").prop("selected",true);
        $("#SPTsearchName").val("");
        getSearchedProjectTasks(me.user_info);
        setTimeout(function(){
            $("#grdSearchTasks").DataTable().draw();
        },200);
    });

    $("#SPTdateType").change(function(){
        getSearchedProjectTasks(me.user_info);
    });

    $("#SPTdateFrom").change(function(){
        getSearchedProjectTasks(me.user_info);
    });

    $("#SPTdateTo").change(function(){
        getSearchedProjectTasks(me.user_info);
    });

    $("#SPTstatus").change(function(){
        getSearchedProjectTasks(me.user_info);
    });

    $("#btnSPTsearch").click(function(){
        getSearchedProjectTasks(me.user_info);
    });

    $("#btnSPTclearSearch").click(function(){
        $("#SPTdateFrom").val(first_day);
        $("#SPTdateTo").val(today);
        $("#SPTdateType option[id=2]").prop("selected",true);
        $("#SPTstatus option[id=1]").prop("selected",true);
        $("#SPTsearchName").val("");
        getSearchedProjectTasks(me.user_info);
    });

    $("#btnSearchTaskDetails").click(function(){
        var table=$("#grdSearchTasks").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            data['task_id']=record['task_id'];
            data['user_id']=me.user_info.user_id;
            data['company_id']=me.user_info.company_id;
            data['user_type_id']=me.user_info.user_type_id;
            data['from']='details';
            $.ajax({
                url:'/task/getTaskDetails',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    try{
                        var res=JSON.parse(response);
                    }catch(err){
                        handleAjaxErrorLoc(1,2,3);
                    }
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

    $("#btnAddSearchedTask").click(function(){
        var task_table=$("#grdSearchTasks").DataTable(); //tabla tareas a buscar
        if (task_table.rows('.selected').any()){
            $.confirm({
                theme:'dark',
                title:'Atención',
                content:'¿Está seguro que desea agregar esta tarea al proyecto?',
                buttons:{
                    confirm:{
                        text:'Sí',
                        action:function(){
                            EasyLoading.show({
                                text:'Cargando...',
                                type:EasyLoading.TYPE['PACMAN'],
                            });
                            var project_table=$("#grdProjects").DataTable(); //tabla de proyectos
                            var project_ind=project_table.row('.selected').index();
                            var project_record=project_table.rows(project_ind).data()[0];
                            var task_ind=task_table.row('.selected').index();
                            var task_record=task_table.rows(task_ind).data()[0];
                            $.ajax({
                                url:'/project/checkTaskProject',
                                method:'POST',
                                data:JSON.stringify({
                                    'task_id':task_record['task_id'],
                                    'project_id':project_record['project_id']
                                }),
                                success:function(response){
                                    EasyLoading.hide();
                                    try{
                                        var res=JSON.parse(response);
                                    }catch(err){
                                        handleAjaxErrorLoc(1,2,3);
                                    }
                                    if (res.success===true){
                                        if (res.needs_confirm===true){
                                            $.confirm({
                                                theme:'dark',
                                                title:'Atención',
                                                content:res.msg_response,
                                                buttons:{
                                                    confirm:{
                                                        text:'Sí',
                                                        action:function(){
                                                            EasyLoading.show({
                                                                text:"Cargando...",
                                                                type:EasyLoading.TYPE["PACMAN"]
                                                            });
                                                            $.ajax({
                                                                url:'/project/addTaskToProject',
                                                                method:'POST',
                                                                data:JSON.stringify({
                                                                    'task_id':task_record['task_id'],
                                                                    'project_id':project_record['project_id'],
                                                                    'user_id':me.user_info.user_id
                                                                }),
                                                                success:function(response2){
                                                                    EasyLoading.hide();
                                                                    try{
                                                                        var res2=JSON.parse(response2);
                                                                    }catch(err){
                                                                        handleAjaxErrorLoc(1,2,3);
                                                                    }
                                                                    if (res2.success){
                                                                        $.alert({
                                                                            theme:'dark',
                                                                            title:'Atención',
                                                                            content:'La tarea ha sido agregada al proyecto.',
                                                                            buttons:{
                                                                                confirm:{
                                                                                    text:'Aceptar',
                                                                                    action:function(){
                                                                                        $("#win_search_project_task").modal("hide");
                                                                                        getProjectTasks(me.user_info,project_record['project_id']);
                                                                                    }
                                                                                }
                                                                            }
                                                                        });
                                                                    }
                                                                    else{
                                                                        $.alert({
                                                                            theme:'dark',
                                                                            title:'Atención',
                                                                            content:res2.msg_response
                                                                        });
                                                                    }
                                                                },
                                                                error:function(){
                                                                    $.alert({
                                                                        theme:'dark',
                                                                        title:'Atención',
                                                                        content:'Ocurrió un error, favor de intentarlo de nuevo.'
                                                                    });
                                                                }
                                                            });
                                                        }
                                                    },
                                                    cancel:{
                                                        text:'No'
                                                    }
                                                }
                                            });
                                        }else{
                                            EasyLoading.show({
                                                text:'Cargando...',
                                                type:EasyLoading.TYPE["PACMAN"]
                                            });
                                            $.ajax({
                                                url:'/project/addTaskToProject',
                                                method:'POST',
                                                data:JSON.stringify({
                                                    'task_id':task_record['task_id'],
                                                    'project_id':project_record['project_id'],
                                                    'user_id':me.user_info.user_id
                                                }),
                                                success:function(response2){
                                                    EasyLoading.hide();
                                                    try{
                                                        var res2=JSON.parse(response2);
                                                    }catch(err){
                                                        handleAjaxErrorLoc(1,2,3);
                                                    }
                                                    if (res2.success){
                                                        $.alert({
                                                            theme:'dark',
                                                            title:'Atención',
                                                            content:'La tarea ha sido agregada al proyecto.',
                                                            buttons:{
                                                                confirm:{
                                                                    text:'Aceptar',
                                                                    action:function(){
                                                                        $("#win_search_project_task").modal("hide");
                                                                        getProjectTasks(me.user_info,project_record['project_id']);
                                                                    }
                                                                }
                                                            }
                                                        });
                                                    }
                                                    else{
                                                        $.alert({
                                                            theme:'dark',
                                                            title:'Atención',
                                                            content:res2.msg_response
                                                        });
                                                    }
                                                },
                                                error:function(){
                                                    $.alert({
                                                        theme:'dark',
                                                        title:'Atención',
                                                        content:'Ocurrió un error, favor de intentarlo de nuevo.'
                                                    });
                                                }
                                            });
                                        }
                                    }else{
                                        $.alert({
                                            theme:'dark',
                                            title:'Atención',
                                            content:res.msg_response
                                        });
                                    }
                                },
                                error:function(){
                                    EasyLoading.hide();
                                    $.alert({
                                        theme:'dark',
                                        title:'Atención',
                                        content:'Ocurrió un error, favor de intentarlo de nuevo.'
                                    });
                                }
                            });
                        }
                    },
                    cancel:{
                        text:'No'
                    }
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

    $("#win_project_detail").on('hidden.bs.modal',function(){
        getProjectGrd(me.user_info);
        $(this).data('project_id',-1);
    });

    $("#btnPrViewTaskDetails").click(function(){
        var table=$("#grdProjectTasks").DataTable();
        if (table.rows('.selected').any()){
            var data={};
            var ind=table.row('.selected').index();
            var record=table.rows(ind).data()[0];
            data['task_id']=record['task_id'];
            data['user_id']=me.user_info.user_id;
            data['company_id']=me.user_info.company_id;
            data['user_type_id']=me.user_info.user_type_id;
            data['from']='details';
            $.ajax({
                url:'/task/getTaskDetails',
                method:'POST',
                data:JSON.stringify(data),
                success:function(response){
                    try{
                        var res=JSON.parse(response);
                    }
                    catch(err){
                        handleAjaxErrorLoc(1,2,3);
                    }
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
                content:'¡Debe seleccionar una tarea para ver sus detalles!'
            });
        }
    });

    $("#btnPrRemoveTask").click(function(){
        var detail_table=$("#grdProjectTasks").DataTable();
        if (detail_table.rows('.selected').any()){
            var detail_ind=detail_table.row('.selected').index();
            var detail_record=detail_table.rows(detail_ind).data()[0];
            $.confirm({
                theme:'dark',
                title:'Atención',
                content:'¿Está seguro que desea eliminar la tarea '+detail_record['name']+' del proyecto?',
                buttons:{
                    confirm:{
                        text:'Sí',
                        action:function(){
                            EasyLoading.show({
                                text:'Cargando...',
                                type:EasyLoading.TYPE["PACMAN"]
                            });
                            var project_table=$("#grdProjects").DataTable();
                            var project_ind=project_table.row('.selected').index();
                            var project_record=project_table.rows(project_ind).data()[0];
                            $.ajax({
                                url:'/project/removeTaskFromProject',
                                method:'POST',
                                data:JSON.stringify({
                                    'user_id':me.user_info.user_id,
                                    'project_id':project_record['project_id'],
                                    'task_id':detail_record['task_id']
                                }),
                                success:function(response){
                                    EasyLoading.hide();
                                    try{
                                        var res=JSON.parse(response);
                                    }
                                    catch(err){
                                        handleAjaxErrorLoc(1,2,3);
                                    }
                                    if (res.success){
                                        getProjectTasks(me.user_info,project_record['project_id']);
                                        $.alert({
                                            theme:'dark',
                                            title:'Atención',
                                            content:res.msg_response
                                        });
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
                                        content:'Ocurrió un error, favor de intentarlo de nuevo más tarde.'
                                    });
                                }
                            });
                        }
                    },
                    cancel:{
                        text:'No'
                    }
                }
            });
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea para eliminarla del proyecto!'
            });
        }
    });

    $("#btnEditProject").click(function(){
        var project_table=$("#grdProjects").DataTable();
        if (project_table.rows('.selected').any()){
            $(this).data('clicked',true);
            var project_ind=project_table.row('.selected').index();
            var project_record=project_table.rows(project_ind).data()[0];
            $("#txtNPname").val(project_record['name']);
            $("#NPdescription").val(project_record['description']);
            var set_date = project_record['deadline'].split("-")[2]+"-"+project_record['deadline'].split("-")[1]+"-"+project_record['deadline'].split("-")[0];
            console.log(set_date);
            $("#NPdeadline").val(set_date);
            $("#win_new_project").modal("show");
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar un proyecto para editarlo!'
            });
        }
    });

    $("#btnDeleteProject").click(function(){
        var project_table=$("#grdProjects").DataTable();
        if (project_table.rows('.selected').any()){
            var project_ind=project_table.row('.selected').index();
            var project_record=project_table.rows(project_ind).data()[0];
            $.confirm({
                theme:'dark',
                title:'Atención',
                content:'Está seguro de eliminar el proyecto '+project_record['name']+' ?',
                buttons:{
                    confirm:{
                        text:'Sí',
                        action:function(){
                            $.ajax({
                                url:'/project/deleteProject',
                                type:'POST',
                                data:JSON.stringify({'project_id':project_record['project_id']}),
                                success:function(response){
                                    try{
                                        var res=JSON.parse(response);
                                    }
                                    catch(err){
                                        handleAjaxErrorLoc(1,2,3);
                                    }
                                    if (res.success){
                                        $.alert({
                                            theme:'dark',
                                            title:'Atención',
                                            content:res.msg_response,
                                            buttons:{
                                                confirm:{
                                                    text:'Aceptar',
                                                    action:function(){
                                                        getProjectGrd(me.user_info);
                                                    }
                                                }
                                            }
                                        });
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
                                        content:'Ocurrió un error, favor de intentarlo más tarde.'
                                    });
                                }
                            });
                        }
                    },
                    cancel:{
                        text:'No',
                        action:function(){

                        }
                    }
                }
            })
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar un proyecto para eliminarlo!'
            });
        }
    });

    $("#btnPrResolveTask").click(function(){
        var task_table=$("#grdProjectTasks").DataTable();
        if (task_table.rows('.selected').any()){
            var task_ind=task_table.row('.selected').index();
            var task_record=task_table.rows(task_ind).data()[0];
            if (task_record['status_id']==1 || task_record['status_id']==6){
                $("#win_resolve_task").data('task_id',task_record['task_id']);
                $("#win_resolve_task").data('status_id',task_record['status_id']);
                var data={};
                data['task_id']=task_record['task_id'];
                data['user_id']=me.user_info.user_id;
                data['company_id']=me.user_info.company_id;
                data['user_type_id']=me.user_info.user_type_id;
                data['from']='resolve';
                $.ajax({
                    url:'/task/getTaskDetails',
                    type:'POST',
                    data:JSON.stringify(data),
                    success:function(response){
                        try{
                            var res=JSON.parse(response);
                        }catch(err){
                            handleAjaxErrorLoc(1,2,3);
                        }
                        if (res.success){
                            $("#RTtask_info").html(res.data);
                            if (res.html_docs.length>0){
                                for (x in res.html_docs){
                                    $("#RTfrmevidences").append(res.html_docs[x]);
                                    if (task_record['status_id']==6){
                                        $("#RTcomments").val(res.comments);
                                    }
                                }
                            }
                            $("#win_resolve_task").modal("show");
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
                            content:'Ocurrió un error, favor de intentarlo más tarde.'
                        });
                    }
                });
            }
            else{
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'Esta tarea no puede ser resuelta.'
                });
            }
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea para poder resolverla!'
            });
        }
    });

    $("#btnPrCheckResolvedTask").click(function(){
        var task_table=$("#grdProjectTasks").DataTable();
        if (task_table.rows('.selected').any()){
            //revisar que esté resuelta o declinada
            var task_ind=task_table.row('.selected').index();
            var task_record=task_table.rows(task_ind).data()[0];
            if (task_record['status_id']==2 || task_record['status_id']==3){
                //validar que no revise la tarea la misma persona que la resolvió
            }
            else{
                $.alert({
                    theme:'dark',
                    title:'Atención',
                    content:'Esta tarea no puede ser revisada.'
                });
            }

        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar una tarea para revisarla!'
            });
        }
    });

    $("#btnSendNotifProject").click(function(){
        var project_table=$("#grdProjects").DataTable();
        if (project_table.rows('.selected').any()){
            var project_ind=project_table.row('.selected').index();
            var project_record=project_table.rows(project_ind).data()[0];
            $("#win_send_project_notification").data('project_id',project_record['project_id']);
            $.ajax({
                url:'/project/getRecipientsInfo',
                type:'POST',
                data:JSON.stringify({'project_id':project_record['project_id'],'user_id':me.user_info.user_id}),
                success:function(response){
                    try{
                        var res=JSON.parse(response);
                    }catch(err){
                        handleAjaxErrorLoc(1,2,3);
                    }
                    if (res.success){
                        $("#SPNfrom").val(res.sender);
                        $("#SPNparentDiv").append(res.divs);
                        $("#win_send_project_notification").modal("show");
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
                        content:'Ocurrió un error, favor de intentarlo de nuevo más tarde.'
                    });
                }
            });

        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar un proyecto para enviar una notificación!'
            });
        }

    });

    $("#btnSendProjNotification").click(function(){
        var notif_info=getDictForm("#frmSendProjectNotif",[],"all");
        console.log(notif_info);
        var send_notif=false;
        Object.keys(notif_info).forEach(function(key) {
            if (key.split("_").length==3){
                if (notif_info[key]==true){
                    send_notif=true;
                }
            }
        });
        if (send_notif===true){
            var project_table=$("#grdProjects").DataTable();
            var project_ind=project_table.row('.selected').index();
            var project_record=project_table.rows(project_ind).data()[0];
            notif_info['sender']=me.user_info.user_id;
            notif_info['project_id']=project_record['project_id'];
            EasyLoading.show({
                text:"Cargando...",
                type:EasyLoading.TYPE["PACMAN"],
            })
            $.ajax({
                url:'/project/sendProjectNotification',
                type:'POST',
                data:JSON.stringify(notif_info),
                success:function(response){
                    EasyLoading.hide();
                    try{
                        var res=JSON.parse(response);
                    }catch(err){
                        handleAjaxErrorLoc(1,2,3);
                    }
                    if (res.success){
                        $.alert({
                            theme:'dark',
                            title:'Atención',
                            content:res.msg_response,
                            buttons:{
                                confirm:{
                                    text:'Aceptar',
                                    action:function(){
                                        $("#win_send_project_notification").modal("hide");
                                    }
                                }
                            }
                        });
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
                        content:'Ocurrió un error, favor de intentarlo de nuevo más tarde.'
                    });
                }
            });
        }
        else{
            $.alert({
                theme:'dark',
                title:'Atención',
                content:'¡Debe seleccionar al menos un destinatario para el mensaje!'
            });
        }
    });

    $("#btnCloseSendProjNotification").click(function(){
        $("#win_send_project_notification").modal("hide");
    });

    $("#win_send_project_notification").on('hidden.bs.modal',function(){
        $("#SPNparentDiv").empty();
        $("#SPNmessage").val("");
        $("#SPNfrom").val("");
        $(this).data('project_id',-1);
    });

    $("#btnShowProjNotifHistory").click(function(){
        var project_id=$("#win_send_project_notification").data('project_id');
        EasyLoading.show({
            text:'Cargando...',
            type:EasyLoading.TYPE["PACMAN"],
        });
        $.ajax({
            url:'/project/getProjectNotificationHistory',
            type:'POST',
            data:JSON.stringify({'project_id':project_id}),
            success:function(response){
                EasyLoading.hide();
                try{
                    var res=JSON.parse(response);
                }catch(err){
                    handleAjaxErrorLoc(1,2,3);
                }
                if (res.success){
                    if (res.has_messages){
                        $("#divProjNotifications").append(res.messages);
                    }
                    else{
                        $("#divProjNotifications").append("<h4>No existen mensajes para esta tarea.</h4>");
                    }
                    $("#win_proj_notif_history").modal("show");
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
                    content:'Ocurrió un error, favor de intentarlo más tarde.'
                });
            }
        });
    });

    $("#btnCloseProjNotifHistory").click(function(){
        $("#win_proj_notif_history").modal("hide");
    });

    $("#win_proj_notif_history").on('hidden.bs.modal',function(){
        $("#divProjNotifications").empty();
    })

});


function collapseProjectFilters(){
    if (window.innerWidth<980){
        $("#divProjectFilters").removeClass('show');
    }
    else{
        $("#divProjectFilters").addClass('show');
    }
}

function getProjectGrd(user_info){
    var sel_list=[{'id':"#PLcreatedBy",'name':"created_by"}];
    var filters=getDictForm("#PLfrmFilters",sel_list);
    filters['date_type']=parseInt($("#PLdateType option:selected")[0].id);
    filters['status_id']=parseInt($("#PLstatus option:selected")[0].id);
    filters['from'],filters['to']=checkDateProject(filters['from'],filters['to']);
    $("#PLdateFrom").val(filters['from']);
    $("#grdProjects").DataTable({
        "scrollY":"225px",
        "scrollCollapse":true,
        "lengthChange":false,
        serverSide:true,
        ajax:{
            data:{
                'company_id':user_info.company_id,
                'user_id':user_info.user_id,
                'user_type_id':user_info.user_type_id,
                'first':false,
                'filter':JSON.stringify(filters)
            },
            url:'/project/getProjects',
            dataSrc:'data',
            type:'POST',
            error:handleAjaxErrorLoc
        },
        columns:[
            {data:'name',"width":"20%"},
            {data:'created_by',"width":"20%"},
            {data:'created',"width":"15%"},
            {data:'deadline',"width":"15%"},
            {data:'tasks',"width":"15%"},
            {data:'status',"width":"15%"}
        ]
    });
}

function getProjectTasks(user_info,project_id){
    $("#grdProjectTasks").DataTable({
        "scrollY":"140px",
        "scrollCollapse":true,
        "lengthChange":false,
        serverSide:true,
        ajax:{
            data:{
                'company_id':user_info.company_id,
                'project_id':project_id
            },
            url:'/project/getProjectTasks',
            dataSrc:'data',
            type:'POST',
            error:handleAjaxErrorLoc
        },
        columns:[
            {data:'name',"width":"30%"},
            {data:'supervisor',"width":"20%"},
            {data:'assignee',"width":"20%"},
            {data:'status',"width":"10%"},
            {data:'deadline',"width":"20%"}
        ]
    });
}

function getSearchedProjectTasks(user_info){
    var filters=getDictForm("#SPTfrmFilters",[]);
    filters['date_type']=parseInt($("#SPTdateType option:selected")[0].id);
    filters['status_id']=parseInt($("#SPTstatus option:selected")[0].id);
    $("#grdSearchTasks").DataTable({
        "scrollY":"160px",
        "scrollCollapse":true,
        "lengthChange":false,
        serverSide:true,
        ajax:{
            data:{
                'company_id':user_info.company_id,
                'user_id':user_info.user_id,
                'user_type_id':user_info.user_type_id,
                'filters':JSON.stringify(filters)
            },
            url:'/project/getSearchedProjectTasks',
            dataSrc:'data',
            type:'POST',
            error: handleAjaxErrorLoc
        },
        columns:[
            {data:'name',"width":"30%"},
            {data:'deadline',"width":"20%"},
            {data:'assignee',"width":"20%"},
            {data:'supervisor',"width":"20%"},
            {data:'status',"width":"10%"}
        ]
    });
}
