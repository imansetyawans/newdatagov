"use client";

import { Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { RecentAuditLog } from "@/components/audit/RecentAuditLog";
import { Button } from "@/components/ui/Button";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import { hasPermission } from "@/lib/permissions";
import type { ApiResponse, CatalogueProject } from "@/lib/types";
import { useAppStore } from "@/store/appStore";

function codeFromName(value: string) {
  return value.trim().toLowerCase().replace(/[^0-9a-zA-Z]+/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<CatalogueProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [categoryDescription, setCategoryDescription] = useState("");
  const [message, setMessage] = useState("");
  const user = useAppStore((state) => state.user);
  const hydrate = useAppStore((state) => state.hydrate);
  const canCreateProject = hasPermission(user, "projects.create");
  const canDisableProject = hasPermission(user, "projects.disable");
  const canManageCategories = hasPermission(user, "projects.manage_categories");

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? projects[0],
    [projects, selectedProjectId]
  );

  async function loadProjects(preferredProjectId = selectedProjectId) {
    try {
      const response = await api.get<ApiResponse<CatalogueProject[]>>("/api/v1/projects", {
        params: { include_inactive: true }
      });
      setProjects(response.data.data);
      if (response.data.data.some((project) => project.id === preferredProjectId)) {
        setSelectedProjectId(preferredProjectId);
      } else if (response.data.data.length) {
        setSelectedProjectId(response.data.data[0].id);
      }
    } catch {
      setMessage("Unable to load projects");
    }
  }

  useEffect(() => {
    hydrate();
    api
      .get<ApiResponse<CatalogueProject[]>>("/api/v1/projects", { params: { include_inactive: true } })
      .then((response) => {
        setProjects(response.data.data);
        if (response.data.data.length) {
          setSelectedProjectId(response.data.data[0].id);
        }
      })
      .catch(() => setMessage("Unable to load projects"));
  }, [hydrate]);

  async function createProject() {
    if (!projectName.trim()) {
      setMessage("Project name is required");
      return;
    }
    try {
      const response = await api.post<ApiResponse<CatalogueProject>>("/api/v1/projects", {
        name: projectName.trim(),
        code: codeFromName(projectName),
        description: projectDescription.trim() || null
      });
      setProjectName("");
      setProjectDescription("");
      setSelectedProjectId(response.data.data.id);
      setMessage("Project created");
      await loadProjects(response.data.data.id);
    } catch {
      setMessage("Unable to create project. Check if the code already exists.");
    }
  }

  async function createCategory() {
    if (!selectedProject || !categoryName.trim()) {
      setMessage("Choose a project and category name first");
      return;
    }
    try {
      await api.post("/api/v1/project-categories", {
        project_id: selectedProject.id,
        name: categoryName.trim(),
        code: codeFromName(categoryName),
        description: categoryDescription.trim() || null
      });
      setCategoryName("");
      setCategoryDescription("");
      setMessage("Category created");
      await loadProjects();
    } catch {
      setMessage("Unable to create category");
    }
  }

  async function toggleProjectStatus(project: CatalogueProject) {
    const nextStatus = project.status === "active" ? "inactive" : "active";
    try {
      await api.patch(`/api/v1/projects/${project.id}`, { status: nextStatus });
      setMessage(`Project ${nextStatus}`);
      await loadProjects();
    } catch {
      setMessage("Unable to update project");
    }
  }

  async function toggleCategoryStatus(categoryId: string, status: string) {
    const nextStatus = status === "active" ? "inactive" : "active";
    try {
      await api.patch(`/api/v1/project-categories/${categoryId}`, { status: nextStatus });
      setMessage(`Category ${nextStatus}`);
      await loadProjects();
    } catch {
      setMessage("Unable to update category");
    }
  }

  return (
    <div className="grid gap-4">
      <section>
        <h1 className="m-0 text-[20px] font-medium">Projects</h1>
        <p className="mt-1 text-[13px] text-[var(--color-text-secondary)]">
          Maintain catalogue project ownership and project-specific asset categories.
        </p>
      </section>

      {message ? <div className="text-[12px] text-[var(--color-brand)]">{message}</div> : null}

      {(canCreateProject || canManageCategories) ? (
      <section className="grid grid-cols-[1fr_1fr] gap-4">
        {canCreateProject ? (
        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <h2 className="m-0 text-[15px] font-medium">Create project</h2>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-1.5 text-[12px] font-medium">
              Project name
              <input
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                placeholder="Loan Origination"
              />
            </label>
            <label className="grid gap-1.5 text-[12px] font-medium">
              Description
              <textarea
                className="min-h-20 rounded-[7px] border border-[var(--color-border)] p-3 text-[13px] font-normal"
                value={projectDescription}
                onChange={(event) => setProjectDescription(event.target.value)}
                placeholder="Project business context"
              />
            </label>
            <Button variant="primary" onClick={createProject}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              Create project
            </Button>
          </div>
        </div>
        ) : null}

        {canManageCategories ? (
        <div className="rounded-[8px] border border-[var(--color-border)] bg-white p-4">
          <h2 className="m-0 text-[15px] font-medium">Create category</h2>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-1.5 text-[12px] font-medium">
              Project
              <select
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
                value={selectedProject?.id ?? ""}
                onChange={(event) => setSelectedProjectId(event.target.value)}
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </label>
            <label className="grid gap-1.5 text-[12px] font-medium">
              Category name
              <input
                className="h-9 rounded-[7px] border border-[var(--color-border)] px-3 text-[13px] font-normal"
                value={categoryName}
                onChange={(event) => setCategoryName(event.target.value)}
                placeholder="Credit Risk"
              />
            </label>
            <label className="grid gap-1.5 text-[12px] font-medium">
              Description
              <textarea
                className="min-h-20 rounded-[7px] border border-[var(--color-border)] p-3 text-[13px] font-normal"
                value={categoryDescription}
                onChange={(event) => setCategoryDescription(event.target.value)}
                placeholder="Category purpose"
              />
            </label>
            <Button variant="primary" onClick={createCategory} disabled={!projects.length}>
              <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
              Create category
            </Button>
          </div>
        </div>
        ) : null}
      </section>
      ) : null}

      <DataTable headers={["Project", "Code", "Assets", "Categories", "Status", "Action"]}>
        {projects.map((project) => (
          <tr key={project.id} className="border-b border-[#F1F5F9] last:border-0">
            <td className="px-4 py-3 text-[12px] font-medium">{project.name}</td>
            <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{project.code}</td>
            <td className="px-4 py-3 text-[12px]">{project.asset_count}</td>
            <td className="px-4 py-3 text-[12px]">{project.categories.length}</td>
            <td className="px-4 py-3 text-[12px] capitalize">{project.status}</td>
            <td className="px-4 py-3">
              {canDisableProject ? (
                <button
                  className="rounded-[7px] border border-[var(--color-border)] px-3 py-1 text-[12px] font-medium text-[var(--color-text-secondary)]"
                  onClick={() => toggleProjectStatus(project)}
                >
                  {project.status === "active" ? "Disable" : "Enable"}
                </button>
              ) : null}
            </td>
          </tr>
        ))}
        {!projects.length ? (
          <tr>
            <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={6}>
              No projects yet. Create a project before assigning catalogue assets.
            </td>
          </tr>
        ) : null}
      </DataTable>

      {selectedProject ? (
        <DataTable headers={[`Categories in ${selectedProject.name}`, "Code", "Assets", "Status", "Action"]}>
          {selectedProject.categories.map((category) => (
            <tr key={category.id} className="border-b border-[#F1F5F9] last:border-0">
              <td className="px-4 py-3 text-[12px] font-medium">{category.name}</td>
              <td className="px-4 py-3 font-mono text-[11px] text-[var(--color-text-secondary)]">{category.code}</td>
              <td className="px-4 py-3 text-[12px]">{category.asset_count}</td>
              <td className="px-4 py-3 text-[12px] capitalize">{category.status}</td>
              <td className="px-4 py-3">
                {canManageCategories ? (
                  <button
                    className="rounded-[7px] border border-[var(--color-border)] px-3 py-1 text-[12px] font-medium text-[var(--color-text-secondary)]"
                    onClick={() => toggleCategoryStatus(category.id, category.status)}
                  >
                    {category.status === "active" ? "Disable" : "Enable"}
                  </button>
                ) : null}
              </td>
            </tr>
          ))}
          {!selectedProject.categories.length ? (
            <tr>
              <td className="px-4 py-8 text-center text-[12px] text-[var(--color-text-muted)]" colSpan={5}>
                No categories in this project yet.
              </td>
            </tr>
          ) : null}
        </DataTable>
      ) : null}

      <RecentAuditLog eventType="catalogue" title="Recent project audit log" />
    </div>
  );
}
