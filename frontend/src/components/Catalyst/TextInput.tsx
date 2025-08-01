import React, { useEffect, useState, useMemo } from "react";
import { debounce } from "lodash";

export default function TextInput({
  value,
  name,
  onChange,
  className = "bg-white/5 text-white block w-full rounded-md border-0 py-1.5 shadow-sm ring-1 ring-inset ring-white/10 focus:ring-2 focus:ring-inset focus:ring-indigo-500 sm:text-sm sm:leading-6"
}: any) {

  const [inputValue, setInputValue] = useState("");

  useEffect(() => {
    if (value) {
      setInputValue(value);
    }
  }, [value]);

  // Debounced onChange
  const debouncedChange = useMemo(
    () => debounce(onChange, 1000), // delay in ms
    [onChange]
  );

  const onChangeHandler = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    debouncedChange(e); // use debounced version
  };

  // Optional: cleanup debounce
  useEffect(() => {
    return () => {
      debouncedChange.cancel();
    };
  }, [debouncedChange]);

  return (
    <input
      type="text"
      name={name}
      disabled={false}
      value={inputValue}
      onChange={onChangeHandler}
      className={className}
    />
  );
}
