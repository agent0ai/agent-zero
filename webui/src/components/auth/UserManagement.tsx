import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  UserPlus,
  Edit,
  Trash2,
  Shield,
  Search,
  Loader2,
} from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
  team: string | null;
  created_at: string;
  last_login: string | null;
}

interface Role {
  id: number;
  name: string;
  description: string;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Create user dialog
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role_ids: [] as number[],
  });
  const [createLoading, setCreateLoading] = useState(false);

  // Edit user dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteUser, setDeleteUser] = useState<User | null>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/auth/users/list', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ skip: 0, limit: 100 }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      setUsers(data.users);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/auth/roles/list', {
        method: 'POST',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch roles');
      }

      const data = await response.json();
      setRoles(data.roles);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchUsers(), fetchRoles()]);
      setLoading(false);
    };
    loadData();
  }, []);

  const handleCreateUser = async () => {
    setCreateLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/users/create', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(createForm),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create user');
      }

      // Reset form and close dialog
      setCreateForm({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role_ids: [],
      });
      setCreateDialogOpen(false);

      // Refresh users list
      await fetchUsers();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteUser) return;

    try {
      const response = await fetch('/api/auth/users/delete', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ user_id: deleteUser.id }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete user');
      }

      setDeleteDialogOpen(false);
      setDeleteUser(null);

      // Refresh users list
      await fetchUsers();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const filteredUsers = users.filter((user) => {
    const search = searchTerm.toLowerCase();
    return (
      user.username.toLowerCase().includes(search) ||
      user.email.toLowerCase().includes(search) ||
      (user.full_name && user.full_name.toLowerCase().includes(search))
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Manage system users, roles, and permissions
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Full Name</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">
                    {user.username}
                    {user.is_superuser && (
                      <Shield className="inline ml-2 h-4 w-4 text-yellow-500" />
                    )}
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.full_name || '-'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {user.roles.map((role) => (
                        <Badge key={role} variant="secondary">
                          {role}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? 'default' : 'secondary'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.last_login
                      ? new Date(user.last_login).toLocaleDateString()
                      : 'Never'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditUser(user);
                          setEditDialogOpen(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setDeleteUser(user);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Add a new user to the system
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="create-username">Username *</Label>
              <Input
                id="create-username"
                value={createForm.username}
                onChange={(e) =>
                  setCreateForm({ ...createForm, username: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-email">Email *</Label>
              <Input
                id="create-email"
                type="email"
                value={createForm.email}
                onChange={(e) =>
                  setCreateForm({ ...createForm, email: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-fullname">Full Name</Label>
              <Input
                id="create-fullname"
                value={createForm.full_name}
                onChange={(e) =>
                  setCreateForm({ ...createForm, full_name: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-password">Password *</Label>
              <Input
                id="create-password"
                type="password"
                value={createForm.password}
                onChange={(e) =>
                  setCreateForm({ ...createForm, password: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateUser} disabled={createLoading}>
              {createLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete user "{deleteUser?.username}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteUser}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
