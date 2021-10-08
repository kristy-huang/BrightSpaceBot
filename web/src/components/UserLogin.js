import React from 'react'

function UserLogin(props) {
    return (
        <div>
            {props.user && props.user.map(user => {
                return (
                    <div key={user.id}>
                        <h2>Hello {user.first_name}</h2>
                    </div>
                )
            })}
        </div>
    )
}

export default UserLogin