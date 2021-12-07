import React, {useState} from 'react'
import {Form, Button} from 'react-bootstrap'
import {Link} from 'react-router-dom'
import {useForm} from 'react-hook-form'
import {useAuth, logout} from '../auth'

function Commands(props) {
    const [loggedIn] = useAuth()
    return (
        <div className="container">
           <table id="commands-table">
              <tr>
                <th id="cell0-0">Command</th>
                <th id="cell0-1">Description</th>
              </tr>
              <tr>
                <td id="cell1-0">hello</td>
                <td id="cell1-1">Greets the user</td>
              </tr>
              <tr>
                <td id="cell2-0">bye</td>
                <td id="cell2-1">Byes the user</td>
              </tr>
              <tr>
                <td id="cell2-0">current storage location</td>
                <td id="cell2-1">Responds with the specific storage path the user wants files to be downloaded to. Returns an error message if no storage path is specified. </td>
              </tr>
              <tr>
                <td id="cell2-0">update storage</td>
                <td id="cell2-1">Allows if the user wants to update their storage path. First asks user if they want google drive or local machine. Afterwards, updates PREFERENCE table to set storage location and storage path. </td>
              </tr>
              <tr>
                <td id="cell2-0">grades: [course name(s)]</td>
                <td id="cell2-1">Gets a letter grade for a class</td>
              </tr>
              <tr>
                <td id="cell2-0">get assignment feedback</td>
                <td id="cell2-1">Allows the user to check and grab feedback for an assignment by providing the course name and assignment name. If feedback exists for a given assignment, the feedback will be outputted to the user in their current channel. If no feedback exists or the query information is invalid, the program will display relevant error messages. </td>
              </tr>
              <tr>
                <td id="cell2-0">search for student</td>
                <td id="cell2-1">Allows the user to search for a student in a given class. User provides course name and student name. If the student name shows up under the list of enrolled users, the bot will confirm that the given student is in the class. If not, then the bot will report to the user that the given student name is not in their specified class. </td>
              </tr>
              <tr>
                <td id="cell2-0">get upcoming quizzes</td>
                <td id="cell2-1">Allows the user to view their upcoming quizzes across all their classes. User simply has to type the command and the bot will find quizzes within a 2-week time period across all their classes. If no quizzes are found, nothing will be outputted to the bot but a simple message. </td>
              </tr>
              <tr>
                <td id="cell2-0">Suggest study groups</td>
                <td id="cell2-1">Allows the user to suggest study groups by making two specifications - number of courses to have in common, and how many students to have in the group. If the user specifies neither of these parameters, then the program will provide a list of the top 3-5 students who have the most courses in common with the user. The user can specify one, both, or none of the parameters when running this program.</td>
              </tr>
              <tr>
                <td id="cell2-0">get busiest weeks</td>
                <td id="cell2-1"></td>
              </tr>
              <tr>
                <td id="cell2-0">get newly graded assignments</td>
                <td id="cell2-1">Returns assignment grades for assignments that were recently graded</td>
              </tr>
              <tr>
                <td id="cell2-0">change bot name</td>
                <td id="cell2-1">Changes the BrightSpace Bot name that appears in the channel where the user is using the Bot.</td>
              </tr>
              <tr>
                <td id="cell2-0">upcoming discussion</td>
                <td id="cell2-1">Tells users of any upcoming discussion posts</td>
              </tr>
              <tr>
                <td id="cell2-0">update notification schedule</td>
                <td id="cell2-1">Add scheduled times the user wants to receive notifications.</td>
              </tr>
              <tr>
                <td id="cell2-0">update notification type</td>
                <td id="cell2-1">Updates the type of notifications that will be sent by the program to the user’s discord channel, when a time that the user scheduled to receive notification comes.</td>
              </tr>
              <tr>
                <td id="cell2-0">delete notifications</td>
                <td id="cell2-1">Delete scheduled times the user wants to receive notifications.</td>
              </tr>
              <tr>
                <td id="cell2-0">check notifications</td>
                <td id="cell2-1">Check scheduled times the user wants to receive notifications.</td>
              </tr>
              <tr>
                <td id="cell2-0">add class schedule</td>
                <td id="cell2-1">Add classes to the user’s class schedule.</td>
              </tr>
              <tr>
                <td id="cell2-0">check class schedule</td>
                <td id="cell2-1">Check the user’s class schedule.</td>
              </tr>
              <tr>
                <td id="cell2-0">Download files:</td>
                <td id="cell2-1">Downloads files from the specified courses in storage path specified in configuration settings.</td>
              </tr>
              <tr>
                <td id="cell2-0">get course priority</td>
                <td id="cell2-1">Gives the course priority that is organized by grades. It will give it in the order where it is whether grade or deadlines</td>
              </tr>
              <tr>
                <td id="cell2-0">overall points: [course name(s)]</td>
                <td id="cell2-1">Gets the overall points for a class (numeric)</td>
              </tr>
              <tr>
                <td id="cell2-0">redirect notifications</td>
                <td id="cell2-1">Allows users to redirect notifications of type grades, deadlines, files, to another text channel.</td>
              </tr>
              <tr>
                <td id="cell2-0">where are my notifications?</td>
                <td id="cell2-1">Lists the text channels the user has made notifications redirect to.</td>
              </tr>
              <tr>
                <td id="cell2-0">add quiz due dates to calendar</td>
                <td id="cell2-1">Adds alls upcoming quizzes to your google calendar</td>
              </tr>
              <tr>
                <td id="cell2-0">get course link</td>
                <td id="cell2-1">Returns all the course links that the user is taking that semester.</td>
              </tr>
              <tr>
                <td id="cell2-0">get upcoming assignments</td>
                <td id="cell2-1">Gives every upcoming assignment in the given user-specific period.</td>
              </tr>
              <tr>
                <td id="cell2-0">suggest course study</td>
                <td id="cell2-1">Gives suggestions of course to study based on user-input which is grade, deadline or deadline, grade.</td>
              </tr>
              <tr>
                <td id="cell2-0">add office hours to calendar</td>
                <td id="cell2-1">Adds offices hours from a specified course into Google Calendar</td>
              </tr>
              <tr>
                <td id="cell2-0">rename file</td>
                <td id="cell2-1">The user can rename a file</td>
              </tr>
              <tr>
                <td id="cell2-0">add discussion schedule</td>
                <td id="cell2-1">add a schedule for when you want to receive reminders to reply to discussion posts</td>
              </tr>
              <tr>
                <td id="cell2-0">check discussion schedule</td>
                <td id="cell2-1">check if you have any discussion posts that you need to reply to</td>
              </tr>
              <tr>
                <td id="cell2-0">archive</td>
                <td id="cell2-1">move past assignments (assignments that are past due date) from the current folder in Google Drive to archive </td>
              </tr>
              <tr>
                <td id="cell2-0">“check update section</td>
                <td id="cell2-1">check to see if an instructor has added a new section to the brightspace course</td>
              </tr>
              <tr>
                <td id="cell2-0">configuration setting</td>
                <td id="cell2-1">Change configuration setting of the bot with one command; useful when the user needs multiple configuration change. </td>
              </tr>
          </table>
        </div>
    )
}

export default Commands