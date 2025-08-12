import { IUserInfo, IConnection } from "../Library/types";

import { TrashIcon } from "@heroicons/react/24/outline";
import { Button } from "../Catalyst/button";
import TextInput from "../Catalyst/TextInput";
import { api } from "@/api";
import { useState, useEffect } from "react";
import { useGetConnections } from "@/hooks";

export const AdminSettings = () => {
const [users, setUsers] = useState<IUserInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Use the connection hook for caching
  const { data: connectionsData, isLoading: connectionsLoading, error: connectionsError } = useGetConnections();
  const connections = connectionsData?.connections || [];

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const usersResponse = await api.getAllUsers();
        const userData = usersResponse?.data || usersResponse || [];
        setUsers(userData);
      } catch (error) {
        console.error("Error fetching users:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleSaveChanges = async () => {
    try {
      await api.bulkUpdateUsers(users);
      setUnsavedChanges(false);
      console.log("Users updated successfully");
    } catch (error) {
      console.error("Error updating users:", error);
    }
  };

  if (loading || connectionsLoading) {
    return <div className="text-white">Loading...</div>;
  }

  if (connectionsError) {
    return <div className="text-red-400">Error loading connections: {connectionsError.message}</div>;
  }

  return (
    <div className="space-y-6">
      <UserList 
        users={users}
        setUsers={setUsers}
        connections={connections}
        setUnsavedChanges={setUnsavedChanges}
      />
      
      {unsavedChanges && (
        <div className="flex justify-end">
          <Button onClick={handleSaveChanges} color="green">
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
};

export const UserList = ({
  users,
  setUsers,
  connections,
  setUnsavedChanges
}: {
  users: IUserInfo[];
  setUsers: React.Dispatch<React.SetStateAction<IUserInfo[]>>;
  connections: IConnection[];
  setUnsavedChanges: React.Dispatch<React.SetStateAction<boolean>>;
}) => {

  const updateUser = (index: number, updates: Partial<IUserInfo>) => {
    const updatedUsers = [...users];
    updatedUsers[index] = { ...updatedUsers[index], ...updates };
    setUsers(updatedUsers);
    setUnsavedChanges(true);
  };

  const addConnectionToUser = (userIndex: number, connectionId: string) => {
    const user = users[userIndex];
    const existingConnections = user.config?.connections || [];
    
    if (!existingConnections.includes(connectionId)) {
      updateUser(userIndex, {
        config: {
          ...user.config,
          connections: [...existingConnections, connectionId]
        }
      });
    }
  };

  const removeConnectionFromUser = (userIndex: number, connectionId: string) => {
    const user = users[userIndex];
    const existingConnections = user.config?.connections || [];
    
    updateUser(userIndex, {
      config: {
        ...user.config,
        connections: existingConnections.filter(id => id !== connectionId)
      }
    });
  };

  const getConnectionName = (connectionId: string) => {
    const connection = connections.find(c => c.id === connectionId);
    return connection ? connection.name : connectionId;
  };

  const getAvailableConnections = (userIndex: number) => {
    const userConnections = users[userIndex].config?.connections || [];
    return connections.filter(c => !userConnections.includes(c.id));
  };

  return (
    <>
      <div className="mt-2 divide-y divide-white/5 rounded-xl bg-white/5">
        <div className="w-full overflow-auto p-6">
          <h2 className="text-lg font-medium text-white mb-4">User Management</h2>
          <table className="w-full text-sm/6 font-medium text-white text-left border-collapse border">
            <thead>
              <tr>
                <th className="px-3 py-2 border-r border-b w-48">Name</th>
                <th className="px-3 py-2 border-r border-b w-64">Email</th>
                <th className="px-3 py-2 border-r border-b w-32">Role</th>
                <th className="px-3 py-2 border-r border-b">Connections</th>
                <th className="px-3 py-2 border-b w-32">Add Connection</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-gray-400">
                    No users found. Check console logs for data.
                  </td>
                </tr>
              ) : (
                users.map((user, userIndex) => (
                  <tr key={user.id || userIndex}>
                      <td className="px-3 py-2 border">
                    <TextInput
                      type="text"
                      value={user.name}
                      onChange={(e: any) => updateUser(userIndex, { name: e.target.value })}
                      className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                    />
                  </td>
                  <td className="px-3 py-2 border">
                    <TextInput
                      type="email"
                      value={user.email || ""}
                      onChange={(e: any) => updateUser(userIndex, { email: e.target.value })}
                      className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                    />
                  </td>
                  <td className="px-3 py-2 border">
                    <select
                      value={user.role}
                      onChange={(e) => updateUser(userIndex, { role: e.target.value })}
                      className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                    >
                      <option value="ADMIN">ADMIN</option>
                      <option value="USER">USER</option>
                    </select>
                  </td>
                  <td className="px-3 py-2 border">
                    <div className="flex flex-wrap gap-2">
                      {(user.config?.connections || []).map((connectionId) => (
                        <div
                          key={connectionId}
                          className="flex items-center bg-slate-600 text-white px-2 py-1 rounded-md text-xs"
                        >
                          <span className="mr-2">{getConnectionName(connectionId)}</span>
                          <button
                            onClick={() => removeConnectionFromUser(userIndex, connectionId)}
                            className="text-white hover:text-red-300"
                          >
                            <TrashIcon className="size-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2 border">
                    <select
                      value=""
                      onChange={(e) => {
                        if (e.target.value) {
                          addConnectionToUser(userIndex, e.target.value);
                          e.target.value = ""; // Reset select
                        }
                      }}
                      className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                    >
                      <option value="">Select connection...</option>
                      {getAvailableConnections(userIndex).map((connection) => (
                        <option key={connection.id} value={connection.id}>
                          {connection.name}
                        </option>
                      ))}
                    </select>
                  </td>
                    </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};