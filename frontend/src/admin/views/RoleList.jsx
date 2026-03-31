import React, { useEffect, useState } from 'react';
import { fetchRoles } from '../models/roleService';

export default function RoleList() {
  const [roles, setRoles] = useState([]);
  useEffect(() => {
    fetchRoles().then(setRoles);
  }, []);
  return (
    <div>
      <h2>Role List</h2>
      <ul>
        {roles.map(r => <li key={r.role_id}>{r.role_name}</li>)}
      </ul>
    </div>
  );
}
