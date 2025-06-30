import { useCallback, useEffect, useState } from "react";
import { IConnectionOptions, IEditConnection } from "@components/Library/types";
import { ArrowPathIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { getRouteApi, useNavigate } from "@tanstack/react-router";
import { AlertIcon, AlertModal } from "@components/Library/AlertModal";
import { enqueueSnackbar } from "notistack";
import {
  useDeleteConnection,
  useGetConnection,
  useGetConversations,
  useUpdateConnection,
  useRefreshConnectionSchema,
  useGenerateDescriptions,
  useGenerateRelationships,
} from "@/hooks";
import { api } from "@/api";
import { Button } from "../Catalyst/button";
import { Transition } from "@headlessui/react";
import { Switch } from "@components/Catalyst/switch";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import {
  PencilSquareIcon
} from "@heroicons/react/24/outline";

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}
const SchemaEditor = ({
  connectionId,
  options,
  setOptions,
}: {
  connectionId: string;
  options: IConnectionOptions;
  setOptions: (newOptions: IConnectionOptions) => void;
}) => {
  const [expanded, setExpanded] = useState(
    Object.fromEntries(options.schemas.map((schema) => [schema.name, false]))
  );
  const [loadingPossibleValuesMap, setLoadingPossibleValuesMap] = useState<Record<string, boolean>>({});
  const [loadingRelationshipsMap, setLoadingRelationshipsMap] = useState<Record<string, boolean>>({});

  const columnFieldChangeHandler = ({ value, name, column_index, table_index, schema_index, relation_index=-1 }: {
    value: unknown, name: string, column_index: number, table_index: number, schema_index: number, relation_index?: number
  }) => {
    const newOptions = structuredClone(options);
    const column = newOptions?.schemas?.[schema_index]?.tables?.[table_index]?.columns?.[column_index];
    if (column) {
      if (relation_index >= 0) {
        if (column.relationship) {
          (column.relationship[relation_index] as Record<string, any>)[name] = value;
        }
      } else {
        (column as any)[name] = value;
      }
    }
    setOptions(newOptions);
  }

  const tableDescriptionFieldChangeHandler = ({ value, table_index, schema_index }: {
    value: unknown, table_index: number, schema_index: number
  }) => {
    const newOptions = structuredClone(options);
    const table = newOptions?.schemas?.[schema_index]?.tables?.[table_index];
    if (table) {
      table.description = value as string;
    }
    setOptions(newOptions);
  }

  const updatePossibleValues = async (connectionId: string, schema_name: string, table_name: string, column_name: string, column_index: number, table_index: number, schema_index: number,) => {
     const key = `${schema_index}-${table_index}-${column_index}`;
    setLoadingPossibleValuesMap(prev => ({ ...prev, [key]: true }));
    try {
      const result = await api.getPossibleValues(connectionId, schema_name, table_name, column_name);
      if (result?.data && Array.isArray(result?.data)) {
        columnFieldChangeHandler({ value: result.data, name: "possible_values", column_index, table_index, schema_index });
      }
    } finally {
      setLoadingPossibleValuesMap(prev => ({ ...prev, [key]: false }));
    }
  }

  const updateRelationships = async (connectionId: string, schema_name: string, table_name: string, column_name: string, column_type: string, column_index: number, table_index: number, schema_index: number,) => {
    const key = `${schema_index}-${table_index}-${column_index}`;
    setLoadingRelationshipsMap(prev => ({ ...prev, [key]: true }));
    try {
      const result = await api.getRelationships(connectionId, schema_name, table_name, column_name, column_type);
      if (result?.data && Array.isArray(result?.data)) {
        columnFieldChangeHandler({ value: result?.data, name: "relationship", column_index, table_index, schema_index });
      }
    } finally {
      setLoadingRelationshipsMap(prev => ({ ...prev, [key]: false }));
    }
  }

  return (
    <div className="mt-2 divide-y divide-white/5 rounded-xl bg-white/5">
      {options.schemas.map((schema, schema_index) =>
        schema.tables.length === 0 ? null : (
          <div className="flex flex-col" key={schema_index}>
            <div className="flex w-full items-center p-6" key={schema_index}>
              <Switch
                color="green"
                name="select_schema"
                checked={schema.enabled}
                onChange={(checked) =>
                  // Check/Uncheck schema and its tables
                  setOptions({
                    schemas: options.schemas.map((prev_schema, prev_idx) =>
                      prev_idx === schema_index
                        ? {
                          ...prev_schema,
                          enabled: checked,
                          tables: prev_schema.tables.map((table) => ({
                            ...table,
                            enabled: checked,
                          })),
                        }
                        : prev_schema
                    ),
                  })
                }
              />
              <div
                className="group flex w-full items-center cursor-pointer"
                onClick={() =>
                  setExpanded((prev) => ({
                    ...prev,
                    [schema.name]: !prev[schema.name],
                  }))
                }
              >
                <span
                  className={classNames(
                    "ml-4 text-sm/6 font-medium group-hover:text-white/80 grow",
                    schema.enabled ? "text-white" : "text-white/50"
                  )}
                >
                  {schema.name}
                </span>
                <ChevronDownIcon
                  className={classNames(
                    "size-5 fill-white/60 group-hover:fill-white/50",
                    expanded[schema.name] ? "rotate-180" : ""
                  )}
                />
              </div>
            </div>

            <Transition show={expanded[schema.name] || false}>
              <div className="transition ease-in-out translate-x-0 data-[closed]:opacity-0 data-[closed]:-translate-y-3">
                {schema.tables.map((table, table_index) => (
                  <div className="p-6 pt-0 pl-12" key={table_index}>
                    <div
                      className="flex w-full items-center"
                      key={schema_index}
                    >
                      <Switch
                        color="green"
                        name="select_schema"
                        checked={table.enabled && schema.enabled}
                        onChange={(checked) =>
                          // Check/Uncheck table
                          setOptions({
                            schemas: options.schemas.map(
                              (prev_schema, prev_idx) =>
                                prev_idx === schema_index
                                  ? {
                                    ...prev_schema,
                                    tables: prev_schema.tables.map(
                                      (table, inner_table_idx) =>
                                        inner_table_idx === table_index
                                          ? {
                                            ...table,
                                            enabled: checked,
                                          }
                                          : table
                                    ),
                                  }
                                  : prev_schema
                            ),
                          })
                        }
                      />

                      <div
                        className="group flex w-full items-center cursor-pointer"
                        onClick={() =>
                          setExpanded((prev) => ({
                            ...prev,
                            [`${schema.name}_${table.name}`]: !prev[`${schema.name}_${table.name}`],
                          }))
                        }
                      >
                        <span
                          className={classNames(
                            "ml-4 text-sm/5",
                            schema.enabled && table.enabled
                              ? "text-white"
                              : "text-white/50"
                          )}
                        >
                          {table.name}
                        </span>
                        {(table?.columns as []).length > 0 &&
                          <span className="mx-1 text-white/70">:</span>
                        }
                        {(table?.columns as []).length > 0 &&
                          <input
                            type="text"
                            name="name"
                            disabled={false}
                            value={table?.description}
                            onChange={(e) => tableDescriptionFieldChangeHandler({ value: e.target.value, table_index, schema_index })}
                            className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                          />}
                        {(table?.columns as []).length > 0 &&
                          <span className="mx-1 text-white/70"></span>
                        }
                        {(table?.columns as []).length > 0 &&
                          <ChevronDownIcon
                            className={classNames(
                              "size-5 fill-white/60 group-hover:fill-white/50",
                              expanded[`${schema.name}_${table.name}`] ? "rotate-180" : ""
                            )}
                          />}
                      </div>
                    </div>
                    {(table?.columns as []).length > 0 && <Transition show={expanded[`${schema.name}_${table.name}`] || false}>
                      <div className="transition ease-in-out translate-x-0 data-[closed]:opacity-0 data-[closed]:-translate-y-3">
                        <div className="w-full overflow-auto pt-5">
                          <table className="w-full text-sm/6 font-medium text-white text-left border-collapse border">
                            <thead>
                              <tr>
                                <th className="px-3 py-2">Enabled</th>
                                <th className="px-3 py-2">Name</th>
                                <th className="px-3 py-2">Description</th>
                                <th className="px-3 py-2">Type</th>
                                <th className="px-3 py-2">Primary Key</th>
                                <th className="px-3 py-2">Possible Values</th>
                                <th className="px-3 py-2">Relationship</th>
                              </tr>
                            </thead>
                            <tbody>
                              {
                                table?.columns?.map((column, column_index) => (
                                  <>
                                    <tr key={column_index}>
                                      <td className="px-3 py-2">
                                        <Switch
                                          color="green"
                                          name="enabled"
                                          checked={column.enabled}
                                          onChange={(value) => columnFieldChangeHandler({ value, name: "enabled", column_index, table_index, schema_index })}
                                        />
                                      </td>
                                      <td className="px-3 py-2">
                                        <input
                                          type="text"
                                          name="name"
                                          disabled={false}
                                          value={column?.name}
                                          onChange={(e) => columnFieldChangeHandler({ value: e.target.value, name: "name", column_index, table_index, schema_index })}
                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                        />
                                      </td>
                                      <td className="px-3 py-2">
                                        <input
                                          type="text"
                                          name="description"
                                          disabled={false}
                                          value={column?.description}
                                          onChange={(e) => columnFieldChangeHandler({ value: e.target.value, name: "description", column_index, table_index, schema_index })}
                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                        />
                                      </td>
                                      <td className="px-3 py-2">
                                        <input
                                          type="text"
                                          name="type"
                                          disabled={false}
                                          value={column?.type}
                                          onChange={(e) => columnFieldChangeHandler({ value: e.target.value, name: "type", column_index, table_index, schema_index })}
                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                        />
                                      </td>
                                      <td className="px-3 py-2">
                                        <Switch
                                          color="green"
                                          name="primary_key"
                                          checked={column.primary_key}
                                          onChange={(value) => columnFieldChangeHandler({ value, name: "primary_key", column_index, table_index, schema_index })}
                                        />
                                      </td>
                                      <td className="px-3 py-2">
                                        <div className="flex items-center gap-x-2">
                                          <input
                                            type="text"
                                            name="possible_values"
                                            disabled={loadingPossibleValuesMap[`${schema_index}-${table_index}-${column_index}`]}
                                            value={column?.possible_values?.join(",")}
                                            // onChange={(e) => columnFieldChangeHandler({ value: (e.target.value || "")?.split(","), name: "possible_values", column_index, table_index, schema_index })}
                                            className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                          />
                                          <Button
                                            onClick={() => updatePossibleValues(connectionId, schema?.name, table?.name, column?.name || "", column_index, table_index, schema_index)}
                                            plain
                                            disabled={loadingPossibleValuesMap[`${schema_index}-${table_index}-${column_index}`]}
                                          >
                                            <ArrowPathIcon
                                              className={classNames(
                                                "w-6 h-6 [&>path]:stroke-[2] group-hover:-rotate-6",
                                                loadingPossibleValuesMap[`${schema_index}-${table_index}-${column_index}`] ? "animate-spin" : ""
                                              )}
                                            />
                                          </Button>
                                        </div>

                                      </td>
                                      <td className="px-3 py-2">
                                        <button
                                          className="text-gray-400 hover:text-white"
                                          onClick={() =>
                                            setExpanded((prev) => ({
                                              ...prev,
                                              [`${schema.name}_${table.name}_${column.name}`]: !prev[`${schema.name}_${table.name}_${column.name}`],
                                            }))
                                          }
                                        >
                                          <PencilSquareIcon className="size-5" />
                                        </button>

                                      </td>
                                    </tr>
                                    <Transition show={expanded[`${schema.name}_${table.name}_${column.name}`] || false}>
                                      <tr className="transition ease-in-out translate-x-0 data-[closed]:opacity-0 data-[closed]:-translate-y-3">
                                        <td className="p-5" colSpan={7}>
                                          <div className="flex items-center gap-x-2">
                                            <h3>Relationship Table</h3>
                                            <Button
                                              onClick={() => updateRelationships(connectionId, schema?.name, table?.name, column?.name || "", column?.type || "", column_index, table_index, schema_index)}
                                              plain
                                              disabled={false}
                                            >
                                              <ArrowPathIcon
                                                className={classNames(
                                                  "w-6 h-6 [&>path]:stroke-[2] group-hover:-rotate-6",
                                                  loadingRelationshipsMap[`${schema_index}-${table_index}-${column_index}`] ? "animate-spin" : ""
                                                )}
                                              />
                                            </Button>
                                          </div>
                                          <div className="w-full overflow-auto pt-2">
                                            <table className="w-full text-sm/6 font-medium text-white text-left border-collapse border">
                                              <thead>
                                                <tr>
                                                  <th className="px-3 py-2">Enabled</th>
                                                  <th className="px-3 py-2">Schema Name</th>
                                                  <th className="px-3 py-2">Table Name</th>
                                                  <th className="px-3 py-2">Column Name</th>
                                                </tr>
                                              </thead>
                                              <tbody>
                                                {
                                                  column?.relationship?.map((relation, relation_index) => (
                                                    <tr key={relation_index}>
                                                      <td className="px-3 py-2">
                                                        <Switch
                                                          color="green"
                                                          name="enabled"
                                                          checked={relation?.enabled}
                                                          onChange={(value) => columnFieldChangeHandler({ value, name: "enabled", column_index, table_index, schema_index, relation_index })}
                                                        />
                                                      </td>
                                                      <td className="px-3 py-2">
                                                        <input
                                                          type="text"
                                                          name="schema_name"
                                                          disabled={false}
                                                          value={relation?.schema_name}
                                                          onChange={(value) => columnFieldChangeHandler({ value, name: "schema_name", column_index, table_index, schema_index, relation_index })}
                                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                                        />
                                                      </td>
                                                      <td className="px-3 py-2">
                                                        <input
                                                          type="text"
                                                          name="table"
                                                          disabled={false}
                                                          value={relation?.table}
                                                          onChange={(value) => columnFieldChangeHandler({ value, name: "table", column_index, table_index, schema_index, relation_index })}
                                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                                        />
                                                      </td>
                                                      <td className="px-3 py-2">
                                                        <input
                                                          type="text"
                                                          name="column"
                                                          disabled={false}
                                                          value={relation?.column}
                                                          onChange={(value) => columnFieldChangeHandler({ value, name: "column", column_index, table_index, schema_index, relation_index })}
                                                          className="bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                                                        />
                                                      </td>
                                                    </tr>
                                                  ))
                                                }
                                              </tbody>
                                            </table>
                                          </div>
                                        </td>
                                      </tr>
                                    </Transition>
                                  </>
                                ))
                              }
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </Transition>}
                  </div>
                ))}
              </div>
            </Transition >
          </div >
        )
      )}
    </div >
  );
};

const connectionRouteApi = getRouteApi("/_app/connection/$connectionId");

export const ConnectionEditor = () => {
  const navigate = useNavigate();
  const { connectionId } = connectionRouteApi.useParams();
  const [unsavedChanges, setUnsavedChanges] = useState<boolean>(false);
  const [showCancelAlert, setShowCancelAlert] = useState<boolean>(false);
  const [showDeleteAlert, setShowDeleteAlert] = useState<boolean>(false);

  const { data, isLoading } = useGetConnection(connectionId);
  const { data: conversationsData } = useGetConversations();
  const relatedConversations =
    conversationsData?.filter(
      (conversation) => conversation.connection_id === connectionId
    ) ?? [];

  const connection = data;

  const { mutate: deleteConnection } = useDeleteConnection({
    onSuccess() {
      navigate({ to: "/" });
    },
  });

  const { mutate: updateConnection,
    isPending: isUpdatingConnection
  } = useUpdateConnection({
    onSuccess() {
      navigate({ to: "/" });
    },
  });

  const { mutate: generateDescriptions,
    isPending: isGeneratingDescriptions
  } = useGenerateDescriptions({
    onSuccess() {
      navigate({ to: "/" });
    },
  });

  const { mutate: generateRelationships,
    isPending: isGeneratingRelationships
  } = useGenerateRelationships({
    onSuccess() {
      navigate({ to: "/" });
    },
  });

  const { mutate: refreshSchema, isPending: isRefreshing } =
    useRefreshConnectionSchema((data) => {
      setEditFields((prev) => ({
        ...prev,
        options: data.options,
      }));
    });

  // Form state
  const [editFields, setEditFields] = useState<IEditConnection>({
    name: "",
    dsn: ""
  });

  useEffect(() => {
    setEditFields((prev) => ({
      name: connection?.name || prev.name,
      dsn: connection?.dsn || prev.dsn,
      options: connection?.options || prev.options,
    }));
  }, [connection]);

  if (!connectionId) {
    enqueueSnackbar({
      variant: "error",
      message: "No connection id provided - something went wrong",
    });
  }

  // Handle navigating back only if there are no unsaved changes
  const handleBack = useCallback(() => {
    if (unsavedChanges) {
      setShowCancelAlert(true);
    } else {
      navigate({ to: "/" });
    }
  }, [navigate, unsavedChanges]);

  // Handle navigating back when escape is pressed
  useEffect(() => {
    const handleKeyPress = (event: { key: string }) => {
      if (event.key === "Escape") {
        handleBack();
      }
    };

    // Add an event listener for the "Escape" key press
    document.addEventListener("keydown", handleKeyPress);

    // Clean up the event listener when the component unmounts
    return () => {
      document.removeEventListener("keydown", handleKeyPress);
    };
  }, [handleBack, unsavedChanges]);

  function handleDelete() {
    if (!connectionId) return;
    deleteConnection(connectionId);
  }

  function handleGenerateDescriptions() {
    if (!connectionId) return;

    generateDescriptions({
      id: connectionId,
      payload: {
        name: editFields.name,
        dsn: editFields.dsn,
        options: editFields.options,
      },
    });
  }

  function handleGenerateRelationships() {
    if (!connectionId) return;

    generateRelationships({
      id: connectionId,
      payload: {
        name: editFields.name,
        dsn: editFields.dsn,
        options: editFields.options,
      },
    });
  }

  function handleSubmit() {
    if (!unsavedChanges) {
      navigate({ to: "/" }); // Return to previous page

      return;
    }

    if (!connectionId) return;

    updateConnection({
      id: connectionId,
      payload: {
        name: editFields.name,
        ...(editFields.dsn !== connection?.dsn && { dsn: editFields.dsn }),
        options: editFields.options,
      },
    });
  }

  return (
    <div className="dark:bg-gray-900 w-full h-full relative flex flex-col mt-16 lg:mt-0">
      <AlertModal
        isOpen={showCancelAlert}
        title="Discard Unsaved Changes?"
        message="You have unsaved changes. Discard changes?"
        okText="OK"
        // color="red"
        icon={AlertIcon.Warning}
        onSuccess={() => {
          setShowCancelAlert(false);
          history.back();
        }}
        onCancel={() => {
          setShowCancelAlert(false);
        }}
      />
      <AlertModal
        isOpen={showDeleteAlert}
        title="Delete Connection?"
        message={`This will delete ${relatedConversations.length} related conversation(s)!`}
        okText="Delete"
        icon={AlertIcon.Warning}
        onSuccess={() => {
          setShowDeleteAlert(false);
          handleDelete();
        }}
        onCancel={() => {
          setShowDeleteAlert(false);
        }}
      />
      <div className="flex flex-col lg:mt-0 p-4 lg:p-24">
        <div className="flex flex-row justify-between">
          <div className="text-gray-50 text-md md:text-2xl font-semibold">
            Edit connection
          </div>
          <div className="cursor-pointer" onClick={handleBack}>
            <XMarkIcon className="w-10 h-10 text-white [&>path]:stroke-[1]" />
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
          <div className="sm:col-span-3">
            <label
              htmlFor="name"
              className="block text-sm font-medium leading-6 text-white"
            >
              Name
            </label>
            <div className="mt-2">
              <input
                type="text"
                name="name"
                id="name"
                disabled={false}
                value={editFields.name}
                onChange={(e) => {
                  setEditFields({ ...editFields, name: e.target.value });
                  setUnsavedChanges(true);
                }}
                className={classNames(
                  isLoading
                    ? "animate-pulse bg-gray-900 text-gray-400"
                    : "bg-white/5 text-white",
                  "block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                )}
              />
            </div>
          </div>

          <div className="sm:col-span-6">
            <label
              htmlFor="name"
              className="block text-sm font-medium leading-6 text-white"
            >
              Database Connection String
            </label>
            <div className="mt-2">
              <input
                type="text"
                name="name"
                id="name"
                disabled={false}
                value={editFields.dsn}
                onChange={(e) => {
                  setEditFields({ ...editFields, dsn: e.target.value });
                  setUnsavedChanges(true);
                }}
                className={classNames(
                  isLoading
                    ? "animate-pulse bg-gray-900 text-gray-400"
                    : "bg-white/5 text-white",
                  "block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
                )}
              />
            </div>
          </div>

          <div className="sm:col-span-6">
            <div className="flex items-center mb-2 gap-x-2">
              <label
                htmlFor="schema"
                className="block text-sm font-medium leading-6 text-white"
              >
                Schema options
              </label>
              <Button
                onClick={() => refreshSchema(connectionId)}
                plain
                disabled={isRefreshing}
              >
                <ArrowPathIcon
                  className={classNames(
                    "w-6 h-6 [&>path]:stroke-[2] group-hover:-rotate-6",
                    isRefreshing ? "animate-spin" : ""
                  )}
                />
              </Button>
            </div>
            {editFields.options && (
              <SchemaEditor
                connectionId={connectionId}
                options={editFields.options}
                setOptions={(newOptions) => {
                  setEditFields((prev) => ({
                    ...prev,
                    options: newOptions,
                  }));
                  setUnsavedChanges(true);
                }}
              />
            )}
          </div>

          <div className="sm:col-span-6 flex items-center justify-end gap-x-6">
            <Button
              color="dark/zinc/sky" disabled={isGeneratingDescriptions}
              // className=" hover:bg-red-700 px-3 py-2 text-sm font-medium text-red-400 hover:text-white border border-gray-600 hover:border-red-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors duration-150"
              onClick={handleGenerateDescriptions}
            >
              {isGeneratingDescriptions ? 'Processing...' : 'Generate Table Descriptions'}
            </Button>
            <Button
              color="dark/zinc/sky" disabled={isGeneratingRelationships}
              // className=" hover:bg-red-700 px-3 py-2 text-sm font-medium text-red-400 hover:text-white border border-gray-600 hover:border-red-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors duration-150"
              onClick={handleGenerateRelationships}
            >
              {isGeneratingRelationships ? 'Processing...' : 'Infer Table Relationships'}
            </Button>
            <Button
              color="dark/zinc/red"
              // className=" hover:bg-red-700 px-3 py-2 text-sm font-medium text-red-400 hover:text-white border border-gray-600 hover:border-red-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors duration-150"
              onClick={() => {
                if (relatedConversations.length > 0) {
                  setShowDeleteAlert(true);
                } else {
                  handleDelete();
                }
              }}
            >
              Delete this connection
            </Button>
            <Button
              onClick={handleBack}
              color="dark/zinc"
            // className="rounded-md bg-gray-600 px-3 py-2 text-sm font-medium text-white border border-gray-500 hover:bg-gray-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors duration-150"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              color="green" disabled={isUpdatingConnection}
            // className="rounded-md px-4 py-2 text-sm font-medium text-white shadow-sm border bg-green-600 border-green-500 hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 transition-colors duration-150"
            >
              {isUpdatingConnection ? 'Processing...' : 'Save'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
