$(document).ready(function(){
  var links=[
    {'href':"../templates/modal/new_company.html", 'id':"#win_register_company"}, //add win company register
    {'href':"../templates/modal/new_admin_user.html", 'id':"#win_new_admin_user"}, //add win new admin/consultant user
    {'href':"../templates/modal/my_account.html", 'id':"#win_my_account"}, //add window my account (user)
    {'href':"../templates/modal/user_change_pass.html", 'id':"#win_change_pass"}, //add window change password
    {'href':"../templates/modal/new-task.html",'id':"#win_new_task"}, //add window new task
    {'href':"../static/modules/user/admin-users.html", 'id':"#win_admin_users"}, //add window user administration
    // {'href':"../static/modules/task/task-list.html",'id':"#win_task_list"}, //add window task list



    // {'href':"../static/modules/settings/notif-rules.html", 'id':"#win_notif_rules"}, //add window notification settings
    // {'href':"../static/modules/settings/company_info.html", 'id':"#win_company_info"}, //add window company info
    // {'href':"../static/modules/settings/logo.html", 'id':"#win_logo"}, //add window logo
    // {'href':"../static/modules/task/task-details.html", 'id':"#win_task_details"}, //add window task details
    // {'href':"../static/modules/task/new-evidence.html", 'id':"#win_new_evidence"}, //add window new evidence

    // {'href':"../static/modules/task/decline_task.html", 'id':"#win_decline_task"}, //add window decline task
    // {'href':"../static/modules/task/resolve_task.html", 'id':"#win_resolve_task"}, //add window resolve task
    // {'href':"../static/modules/user/new_user.html", 'id':"#win_new_user"} //add window new user/edit user

  ];
  for (var x in links){
    var href='link[href="'+links[x]['href']+'"]';
    var l=document.querySelector(href);
    var win_id=links[x]['id'];
    document.body.appendChild(l.import.body.querySelector(win_id));
  }


});
