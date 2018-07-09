$(document).ready(function(){
    var me = this;
    this.user_info=JSON.parse($("#spnSession")[0].textContent);

    $("#btnSaveNotifSettings").click(function(){
        var data={};
        data['admin_report_frequency']=$("#NSadmin_report_frequency option:selected")[0].id;
        data['assignee_days']=$("#NSassignee_days option:selected")[0].id;
        data['supervisor_days']=$("#NSsupervisor_days option:selected")[0].id;
        data['admin_days']=$("#NSadmin_days option:selected")[0].id;
        console.log(data);
        data['company_id']=me.user_info.company_id;
        EasyLoading.show({
            text:'Cargando...',
            type:EasyLoading.TYPE["PACMAN"]
        });
        $.ajax({
            url:'/settings/saveNotificationSettings',
            method:'POST',
            data:JSON.stringify(data),
            success:function(response){
                var res=JSON.parse(response);
                EasyLoading.hide();
                if (res.success){
                    $("#win_notification_settings").modal("hide");
                    $("#alertLayout").find('p').html(res.msg_response);
                    $("#alertLayout").css("display","block");
                }
                else{
                    setMessage("#alertNSForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                }
            },
            error:function(){
                EasyLoading.hide();
                setMessage("#alertNSForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
            }
        });
    });

    $("#win_notification_settings").on('show.bs.modal',function(){
        EasyLoading.show({
            text:'Cargando...',
            type:EasyLoading.TYPE["PACMAN"]
        });
        $.ajax({
            url:'/settings/getNotificationSettings',
            method:'POST',
            data:JSON.stringify({'company_id':me.user_info.company_id}),
            success:function(response){
                var res=JSON.parse(response);
                EasyLoading.hide();
                if (res.success){
                    if (res.has_info){
                        $("#NSadmin_report_frequency option[id="+res.data['admin_report_frequency']+"]").prop("selected",true);
                        $("#NSassignee_days option[id="+res.data['assignee_days']+"]").prop("selected",true);
                        $("#NSsupervisor_days option[id="+res.data['supervisor_days']+"]").prop("selected",true);
                        $("#NSadmin_days option[id="+res.data['admin_days']+"]").prop("selected",true);
                    }
                }
                else{
                    setMessage("#alertNSForm",["alert-info","alert-success"],"alert-danger",res.msg_response,true);
                }
            },
            error:function(){
                EasyLoading.hide();
                setMessage("#alertNSForm",["alert-info","alert-success"],"alert-danger","Ocurrió un error, favor de intentarlo de nuevo.",true);
            }
        });
    });

    $("#btnCloseNotifSettings").click(function(){
        $("#win_notification_settings").modal("hide");
        $("#NSadmin_report_frequency option[id=1_d]").prop("selected",true);
        $("#NSassignee_days option[id=1_d]").prop("selected",true);
        $("#NSsupervisor_days option[id=1_d]").prop("selected",true);
        $("#NSadmin_days option[id=1_d]").prop("selected",true);
    });

});
