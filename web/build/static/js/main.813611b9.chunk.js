(this.webpackJsonpweb=this.webpackJsonpweb||[]).push([[0],{35:function(e,t,s){},36:function(e,t,s){},45:function(e,t,s){},47:function(e,t,s){"use strict";s.r(t);var c=s(1),r=s.n(c),n=s(27),i=s.n(n),a=(s(35),s(36),s(6)),l=s(9),o=s(28),d=Object(o.createAuthProvider)({accessTokenKey:"access_token",onUpdateToken:function(e){return fetch("/refresh",{method:"POST",body:e.refresh_token}).then((function(e){return e.json()}))}}),j=Object(a.a)(d,4),h=j[0],b=(j[1],j[2]),u=j[3],O=s.p+"static/media/Brightspacebot.a4941299.png",x=s(0);function m(){return Object(x.jsx)("div",{children:Object(x.jsx)("p",{children:"You are logged in"})})}function p(){return Object(x.jsxs)(x.Fragment,{children:[Object(x.jsx)("h1",{children:"Welcome to BrightSpaceBot"}),Object(x.jsx)("br",{}),Object(x.jsx)("br",{}),Object(x.jsx)("p",{children:"Many college students utilize the online platform, BrightSpace, for accessing class content and managing assignments. Downloading lectures, documents, and checking due dates are frequently executed tasks that students spend too much time doing. For example, currently students must manually navigate to each class page and filter through all folders set up by their professor in order to download the appropriate resources to complete assignments. The BrightspaceBot aims to automate these redundant tasks, so that students are well prepared for their classes."}),Object(x.jsx)("br",{}),Object(x.jsx)("br",{}),Object(x.jsx)(l.b,{to:"/register",className:"btn btn-primary",children:"Get Started"})]})}var g=function(e){var t=h(),s=Object(a.a)(t,1)[0];return Object(x.jsxs)("div",{className:"home container",children:[Object(x.jsx)("img",{src:O,height:200,width:480}),Object(x.jsx)("br",{}),Object(x.jsx)("br",{}),s?Object(x.jsx)(m,{}):Object(x.jsx)(p,{})]})},f=s(2),v=s(48),w=s(49),y=s(17),N=s(8);var k=function(e){var t=Object(y.a)(),s=t.register,c=(t.watch,t.handleSubmit),r=t.reset,n=t.formState.errors,i=Object(N.f)();return Object(x.jsx)("div",{className:"container",children:Object(x.jsxs)("div",{className:"form",children:[Object(x.jsx)("h1",{children:"Login Page"}),Object(x.jsx)("br",{}),Object(x.jsxs)("form",{children:[Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Username"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"text",placeholder:"Username"},s("username",{required:!0,maxLength:50}))),n.username&&Object(x.jsx)("span",{style:{color:"red"},children:"Username is required"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Password"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"password",placeholder:"Password"},s("password",{required:!0,minLength:6}))),n.password&&Object(x.jsx)("span",{style:{color:"red"},children:"Password is required"})]}),Object(x.jsx)("br",{}),Object(x.jsx)(v.a.Group,{children:Object(x.jsx)(w.a,{as:"sub",variant:"primary",onClick:c((function(e){console.log(e),sessionStorage.setItem("username",e.username);var t={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:e.username,password:e.password})};fetch("/login",t).then((function(e){return e.json()})).then((function(e){200===e.status?(b(e.access_token),i.push("/")):"User not found"===e.message?(i.push("register"),alert("User not found. Please register for an account.")):"Wrong password"===e.message?alert("Wrong password. Please try again."):alert(e.message)})).catch((function(e){return console.log(e)})),r()})),children:"Login"})}),Object(x.jsx)("br",{}),Object(x.jsx)(v.a.Group,{children:Object(x.jsxs)("small",{children:["Don't have an account? ",Object(x.jsx)(l.b,{to:"/register",children:"Create one"})]})})]})]})})};function L(){return Object(x.jsxs)(x.Fragment,{children:[Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link active","aria-current":"page",to:"/",children:"Home"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link active","aria-current":"page",to:"/updateProfile",children:"Update Profile"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link",to:"/getBot",children:"Get Bot"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)("a",{className:"nav-link",onClick:function(){return u()},children:"Log Out"})})]})}function C(){return Object(x.jsxs)(x.Fragment,{children:[Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link active","aria-current":"page",to:"/",children:"Home"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link",to:"/commands",children:"Commands"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link",to:"/register",children:"Sign Up"})}),Object(x.jsx)("li",{className:"nav-item",children:Object(x.jsx)(l.b,{className:"nav-link",to:"/login",children:"Login"})})]})}var q=function(){var e=h(),t=Object(a.a)(e,1)[0];return Object(x.jsx)("nav",{className:"navbar navbar-expand-lg navbar-light bg-light",children:Object(x.jsxs)("div",{className:"container-fluid",children:[Object(x.jsx)(l.b,{className:"navbar-brand",to:"/",children:"BrightSpaceBot"}),Object(x.jsx)("button",{className:"navbar-toggler",type:"button","data-bs-toggle":"collapse","data-bs-target":"#navbarNav","aria-controls":"navbarNav","aria-expanded":"false","aria-label":"Toggle navigation",children:Object(x.jsx)("span",{className:"navbar-toggler-icon"})}),Object(x.jsx)("div",{className:"collapse navbar-collapse",id:"navbarNav",children:Object(x.jsx)("ul",{className:"navbar-nav",children:t?Object(x.jsx)(L,{}):Object(x.jsx)(C,{})})})]})})};var P=function(e){var t,s,c=Object(y.a)(),r=c.register,n=(c.watch,c.handleSubmit),i=c.reset,a=c.formState.errors;return Object(x.jsx)("div",{className:"container",children:Object(x.jsxs)("div",{className:"form",children:[Object(x.jsx)("h1",{children:"Sign Up Page"}),Object(x.jsx)("br",{}),Object(x.jsxs)("form",{children:[Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"First Name"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"text",placeholder:"First Name"},r("firstName",{required:!0,maxLength:50}))),a.firstName&&Object(x.jsx)("span",{style:{color:"red"},children:"First name is required"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Last Name"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"text",placeholder:"Last Name"},r("lastName",{required:!0,maxLength:50}))),a.lastName&&Object(x.jsx)("span",{style:{color:"red"},children:"Last name is required"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Major"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"text",placeholder:"Major"},r("major",{required:!0,maxLength:50}))),a.major&&Object(x.jsx)("span",{style:{color:"red"},children:"Major is required."})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Username"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"text",placeholder:"Username"},r("username",{required:!0,maxLength:50}))),a.username&&Object(x.jsx)("span",{style:{color:"red"},children:"Username is required"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Password"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"password",placeholder:"Password"},r("password",{required:!0,minLength:6}))),a.password&&Object(x.jsx)("span",{style:{color:"red"},children:"Password is required."}),"minLength"===(null===(t=a.password)||void 0===t?void 0:t.type)&&Object(x.jsx)("span",{style:{color:"red"},children:" Passwords should have at least 6 characters"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Confirm Password"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"password",placeholder:"Confirm Password"},r("confirmPassword",{required:!0,minLength:6}))),a.confirmPassword&&Object(x.jsx)("span",{style:{color:"red"},children:"Confirm password is required."}),"minLength"===(null===(s=a.confirmPassword)||void 0===s?void 0:s.type)&&Object(x.jsx)("span",{style:{color:"red"},children:" Passwords should have at least 6 characters"})]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Choose a Storage Location"}),Object(x.jsxs)(v.a.Select,Object(f.a)(Object(f.a)({},r("storageLocation",{required:!0})),{},{children:[Object(x.jsx)("option",{value:"Google Drive",children:"Google Drive"}),Object(x.jsx)("option",{value:"Local Machine",children:"Local Machine"})]}))]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Configure Your Notification Frequency"}),Object(x.jsxs)(v.a.Select,Object(f.a)(Object(f.a)({},r("notificationFrequency",{required:!0})),{},{children:[Object(x.jsx)("option",{value:"1",children:"Every 4 hours"}),Object(x.jsx)("option",{value:"2",children:"Every 6 hours"}),Object(x.jsx)("option",{value:"3",children:"Once a day"}),Object(x.jsx)("option",{value:"4",children:"Once a week"}),Object(x.jsx)("option",{value:"5",children:"Custom"})]}))]}),Object(x.jsx)(v.a.Group,{children:Object(x.jsx)(w.a,{as:"sub",variant:"primary",onClick:n((function(e){if(console.log(e),e.password===e.confirmPassword){var t={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:e.username,firstName:e.firstName,lastName:e.lastName,password:e.password,major:e.major,storageLocation:e.storageLocation,notificationFrequency:e.notificationFrequency})};console.log(t),fetch("/registerUser",t).then((function(e){return e.json()})).then((function(e){return alert(e.message)})).catch((function(e){return console.log(e)})),i()}else alert("Passwords do not match")})),children:"Sign up"})})]})]})})};function G(){var e=Object(y.a)(),t=e.register,s=(e.watch,e.handleSubmit),c=e.reset;e.formState.errors;return Object(x.jsx)(x.Fragment,{children:Object(x.jsxs)("div",{className:"form",children:[Object(x.jsx)("h1",{children:"Update Profile"}),Object(x.jsx)("br",{}),Object(x.jsxs)("form",{children:[Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Major"}),Object(x.jsx)(v.a.Control,Object(f.a)({type:"major",placeholder:"Major"},t("major")))]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Storage Location"}),Object(x.jsxs)(v.a.Select,Object(f.a)(Object(f.a)({},t("storageLocation")),{},{children:[Object(x.jsx)("option",{value:"-1",children:"--"}),Object(x.jsx)("option",{value:"Google Drive",children:"Google Drive"}),Object(x.jsx)("option",{value:"Local Machine",children:"Local Machine"})]}))]}),Object(x.jsx)("br",{}),Object(x.jsxs)(v.a.Group,{children:[Object(x.jsx)(v.a.Label,{children:"Notification Frequency"}),Object(x.jsxs)(v.a.Select,Object(f.a)(Object(f.a)({},t("notificationFrequency")),{},{children:[Object(x.jsx)("option",{value:"-1",children:"--"}),Object(x.jsx)("option",{value:"1",children:"Every 4 hours"}),Object(x.jsx)("option",{value:"2",children:"Every 6 hours"}),Object(x.jsx)("option",{value:"3",children:"Once a day"}),Object(x.jsx)("option",{value:"4",children:"Once a week"}),Object(x.jsx)("option",{value:"5",children:"Custom"})]}))]}),Object(x.jsx)(v.a.Group,{children:Object(x.jsx)(w.a,{as:"sub",variant:"primary",onClick:s((function(e){var t,s=sessionStorage.getItem("username");console.log(s),console.log(e),t=""===e.major?"-1":e.major;var r={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:s,major:t,storageLocation:e.storageLocation,notificationFrequency:e.notificationFrequency})};fetch("/updateProfile",r).then((function(e){return e.json()})).then((function(e){alert(e.message)})).catch((function(e){return console.log(e)})),c()})),children:"Update"})}),Object(x.jsx)("br",{}),Object(x.jsx)(v.a.Group,{children:Object(x.jsx)(w.a,{as:"sub",variant:"primary",children:Object(x.jsx)(l.b,{className:"nav-link active","aria-current":"page",to:"/",children:"Cancel"})})})]})]})})}function S(){return Object(x.jsx)(x.Fragment,{children:Object(x.jsx)("p",{children:"Please login to see this page"})})}var F=function(e){var t=h(),s=Object(a.a)(t,1)[0];return Object(x.jsx)("div",{className:"container",children:s?Object(x.jsx)(G,{}):Object(x.jsx)(S,{})})};function B(){return Object(x.jsxs)(x.Fragment,{children:[Object(x.jsx)("h1",{children:"Instructions"}),Object(x.jsx)("p",{children:"1. Create a server on Discord"}),Object(x.jsx)("p",{children:"2. Click the link below to get bot and select the server you want to add your bot to"}),Object(x.jsx)("a",{href:"https://discord.com/api/oauth2/authorize?client_id=894695859567083520&permissions=534992387152&scope=bot",target:"_blank",children:"Get Bot"})]})}function U(){return Object(x.jsx)(x.Fragment,{children:Object(x.jsx)("p",{children:"Please login to see this page"})})}var T=function(e){var t=h(),s=Object(a.a)(t,1)[0];return Object(x.jsx)("div",{className:"container",children:s?Object(x.jsx)(B,{}):Object(x.jsx)(U,{})})};var z=function(e){var t=h();return Object(a.a)(t,1)[0],Object(x.jsx)("div",{className:"container",children:Object(x.jsxs)("table",{id:"commands-table",children:[Object(x.jsxs)("tr",{children:[Object(x.jsx)("th",{id:"cell0-0",children:"Command"}),Object(x.jsx)("th",{id:"cell0-1",children:"Description"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell1-0",children:"hello"}),Object(x.jsx)("td",{id:"cell1-1",children:"Greets the user"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"bye"}),Object(x.jsx)("td",{id:"cell2-1",children:"Byes the user"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"current storage location"}),Object(x.jsx)("td",{id:"cell2-1",children:"Responds with the specific storage path the user wants files to be downloaded to. Returns an error message if no storage path is specified. "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"update storage"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows if the user wants to update their storage path. First asks user if they want google drive or local machine. Afterwards, updates PREFERENCE table to set storage location and storage path. "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"grades: [course name(s)]"}),Object(x.jsx)("td",{id:"cell2-1",children:"Gets a letter grade for a class"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get assignment feedback"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows the user to check and grab feedback for an assignment by providing the course name and assignment name. If feedback exists for a given assignment, the feedback will be outputted to the user in their current channel. If no feedback exists or the query information is invalid, the program will display relevant error messages. "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"search for student"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows the user to search for a student in a given class. User provides course name and student name. If the student name shows up under the list of enrolled users, the bot will confirm that the given student is in the class. If not, then the bot will report to the user that the given student name is not in their specified class. "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get upcoming quizzes"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows the user to view their upcoming quizzes across all their classes. User simply has to type the command and the bot will find quizzes within a 2-week time period across all their classes. If no quizzes are found, nothing will be outputted to the bot but a simple message. "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"Suggest study groups"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows the user to suggest study groups by making two specifications - number of courses to have in common, and how many students to have in the group. If the user specifies neither of these parameters, then the program will provide a list of the top 3-5 students who have the most courses in common with the user. The user can specify one, both, or none of the parameters when running this program."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get busiest weeks"}),Object(x.jsx)("td",{id:"cell2-1"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get newly graded assignments"}),Object(x.jsx)("td",{id:"cell2-1",children:"Returns assignment grades for assignments that were recently graded"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"change bot name"}),Object(x.jsx)("td",{id:"cell2-1",children:"Changes the BrightSpace Bot name that appears in the channel where the user is using the Bot."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"upcoming discussion"}),Object(x.jsx)("td",{id:"cell2-1",children:"Tells users of any upcoming discussion posts"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"update notification schedule"}),Object(x.jsx)("td",{id:"cell2-1",children:"Add scheduled times the user wants to receive notifications."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"update notification type"}),Object(x.jsx)("td",{id:"cell2-1",children:"Updates the type of notifications that will be sent by the program to the user\u2019s discord channel, when a time that the user scheduled to receive notification comes."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"delete notifications"}),Object(x.jsx)("td",{id:"cell2-1",children:"Delete scheduled times the user wants to receive notifications."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"check notifications"}),Object(x.jsx)("td",{id:"cell2-1",children:"Check scheduled times the user wants to receive notifications."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"add class schedule"}),Object(x.jsx)("td",{id:"cell2-1",children:"Add classes to the user\u2019s class schedule."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"check class schedule"}),Object(x.jsx)("td",{id:"cell2-1",children:"Check the user\u2019s class schedule."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"Download files:"}),Object(x.jsx)("td",{id:"cell2-1",children:"Downloads files from the specified courses in storage path specified in configuration settings."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get course priority"}),Object(x.jsx)("td",{id:"cell2-1",children:"Gives the course priority that is organized by grades. It will give it in the order where it is whether grade or deadlines"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"overall points: [course name(s)]"}),Object(x.jsx)("td",{id:"cell2-1",children:"Gets the overall points for a class (numeric)"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"redirect notifications"}),Object(x.jsx)("td",{id:"cell2-1",children:"Allows users to redirect notifications of type grades, deadlines, files, to another text channel."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"where are my notifications?"}),Object(x.jsx)("td",{id:"cell2-1",children:"Lists the text channels the user has made notifications redirect to."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"add quiz due dates to calendar"}),Object(x.jsx)("td",{id:"cell2-1",children:"Adds alls upcoming quizzes to your google calendar"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get course link"}),Object(x.jsx)("td",{id:"cell2-1",children:"Returns all the course links that the user is taking that semester."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"get upcoming assignments"}),Object(x.jsx)("td",{id:"cell2-1",children:"Gives every upcoming assignment in the given user-specific period."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"suggest course study"}),Object(x.jsx)("td",{id:"cell2-1",children:"Gives suggestions of course to study based on user-input which is grade, deadline or deadline, grade."})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"add office hours to calendar"}),Object(x.jsx)("td",{id:"cell2-1",children:"Adds offices hours from a specified course into Google Calendar"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"rename file"}),Object(x.jsx)("td",{id:"cell2-1",children:"The user can rename a file"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"add discussion schedule"}),Object(x.jsx)("td",{id:"cell2-1",children:"add a schedule for when you want to receive reminders to reply to discussion posts"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"check discussion schedule"}),Object(x.jsx)("td",{id:"cell2-1",children:"check if you have any discussion posts that you need to reply to"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"archive"}),Object(x.jsx)("td",{id:"cell2-1",children:"move past assignments (assignments that are past due date) from the current folder in Google Drive to archive "})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"\u201ccheck update section"}),Object(x.jsx)("td",{id:"cell2-1",children:"check to see if an instructor has added a new section to the brightspace course"})]}),Object(x.jsxs)("tr",{children:[Object(x.jsx)("td",{id:"cell2-0",children:"configuration setting"}),Object(x.jsx)("td",{id:"cell2-1",children:"Change configuration setting of the bot with one command; useful when the user needs multiple configuration change. "})]})]})})};s(45);var A=function(){return Object(x.jsx)(l.a,{children:Object(x.jsxs)("div",{className:"App",children:[Object(x.jsx)(q,{}),Object(x.jsxs)(N.c,{children:[Object(x.jsx)(N.a,{path:"/login",children:Object(x.jsx)(k,{})}),Object(x.jsx)(N.a,{path:"/commands",children:Object(x.jsx)(z,{})}),Object(x.jsx)(N.a,{path:"/register",children:Object(x.jsx)(P,{})}),Object(x.jsx)(N.a,{path:"/updateProfile",children:Object(x.jsx)(F,{})}),Object(x.jsx)(N.a,{path:"/getBot",children:Object(x.jsx)(T,{})}),Object(x.jsx)(N.a,{path:"/",children:Object(x.jsx)(g,{})})]})]})})},D=function(e){e&&e instanceof Function&&s.e(3).then(s.bind(null,50)).then((function(t){var s=t.getCLS,c=t.getFID,r=t.getFCP,n=t.getLCP,i=t.getTTFB;s(e),c(e),r(e),n(e),i(e)}))};s(46);i.a.render(Object(x.jsx)(r.a.StrictMode,{children:Object(x.jsx)(A,{})}),document.getElementById("root")),D()}},[[47,1,2]]]);
//# sourceMappingURL=main.813611b9.chunk.js.map