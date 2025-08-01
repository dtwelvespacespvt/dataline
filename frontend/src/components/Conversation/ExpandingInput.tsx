import {
  PaperAirplaneIcon,
  Cog6ToothIcon,
  ShieldExclamationIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";
import {
  SetStateAction,
  forwardRef,
  useRef,
  useState,
  useEffect,
} from "react";
import { Switch, SwitchField, SwitchGroup } from "../Catalyst/switch";
import { Description, Fieldset, Label } from "../Catalyst/fieldset";
import { Transition } from "@headlessui/react";

import {
  useGetRelatedConnection,
  getMessageOptions,
  usePatchMessageOptions,
} from "@/hooks";
import { useClickOutside } from "../Library/utils";
import { useQuery } from "@tanstack/react-query";

type ExpandingInputProps = {
  onSubmit: (value: string) => void;
  disabled: boolean;
  autoCompleteList: any;
};

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

type MessageSettingsPopupProps = {
  isShown: boolean;
  setIsShown: (val: boolean) => void;
  settingsCogRef: React.MutableRefObject<HTMLDivElement | null>;
};

const MessageSettingsPopup: React.FC<MessageSettingsPopupProps> = ({
  isShown,
  setIsShown,
  settingsCogRef: cogRef,
}) => {
  const currConnection = useGetRelatedConnection();
  const { data: messageOptions } = useQuery(
    getMessageOptions(currConnection?.id)
  );
  const { mutate: patchMessageOptions } = usePatchMessageOptions(
    currConnection?.id
  );
  const settingsPopupRef = useRef<HTMLDivElement | null>(null);
  useClickOutside([settingsPopupRef, cogRef], () => {
    setIsShown(false);
  });

  return (
    <Transition
      show={isShown}
      enter="transition-opacity duration-200"
      enterFrom="opacity-0"
      enterTo="opacity-100"
      leave="transition-opacity duration-200"
      leaveFrom="opacity-100"
      leaveTo="opacity-0"
    >
      <div
        ref={settingsPopupRef}
        className="absolute left-0 bottom-1 border p-4 bg-gray-900 border-gray-600 rounded-xl"
      >
        <Fieldset>
          <SwitchGroup>
            <SwitchField>
              <Label className="flex items-center">Data Security </Label>
              <Description>Hide your data from the AI model</Description>
              <Switch
                color="green"
                checked={messageOptions?.secure_data}
                onChange={(checked) =>
                  patchMessageOptions({ secure_data: checked })
                }
                name="data_security"
              />
            </SwitchField>
          </SwitchGroup>
        </Fieldset>
      </div>
    </Transition>
  );
};

const ExpandingInput = forwardRef<HTMLTextAreaElement, ExpandingInputProps>(
  ({ onSubmit, disabled, autoCompleteList }, ref) => {
    const [inputValue, setInputValue] = useState("");
    const [messageSettingsShown, setMessageSettingsShown] = useState(false);
    const currConnection = useGetRelatedConnection();
    const { data: messageOptions } = useQuery(
      getMessageOptions(currConnection?.id)
    );
    const settingsCogRef = useRef<HTMLDivElement | null>(null);

    const suggestions = Object.keys(autoCompleteList || {});
    const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>(
      []
    );
    const [showSuggestions, setShowSuggestions] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      setInputValue(value);
      e.target.style.height = "auto";
      e.target.style.height = `${e.target.scrollHeight}px`;

      const cursorPos = e.target.selectionStart;
      const textBeforeCursor = value.slice(0, cursorPos);
      const match = textBeforeCursor.match(/(\w{3,})$/);

      if (match) {
        const query = match[1].toLowerCase();
        const filtered = suggestions.filter((s) =>
          s.toLowerCase().includes(query)
        );
        setFilteredSuggestions(filtered);
        setShowSuggestions(filtered.length > 0);
      } else {
        setShowSuggestions(false);
      }
    };

    // const handleSubmit = () => {
    //   if (disabled || inputValue.length === 0) return;
    //   onSubmit(inputValue);
    //   setInputValue("");
    //   setShowSuggestions(false);
    // };

    const handleSubmit = () => {
      if (disabled || inputValue.length === 0) return;

      let transformed = inputValue;

      // Sort tags by length descending so longer phrases match first
      const sortedTags = suggestions.sort((a, b) => b.length - a.length);

      for (const tag of sortedTags) {
        const tagRegex = new RegExp(`\\b${tag.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, "gi");
        const tags = autoCompleteList[tag];

        if (tags.includes("uniqueKey")) {
          transformed = transformed.replace(tagRegex, `[${tag}]`);
        } else if (tags.includes("glossary")) {
          transformed = transformed.replace(tagRegex, `<${tag}>`);
        }
      }
      
      onSubmit(transformed);
      setInputValue("");
      setShowSuggestions(false);
    };


    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
        e.currentTarget.style.height = "auto";
      }
    };

    const insertSuggestionAtCaret = (suggestion: string) => {
      const textarea = ref && "current" in ref ? ref.current : null;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;

      const textBefore = inputValue.substring(0, start);
      const textAfter = inputValue.substring(end);

      const match = textBefore.match(/(\w{3,})$/);
      const replaceStart = match ? start - match[1].length : start;

      const newValue =
        inputValue.substring(0, replaceStart) +
        suggestion +
        " " +
        textAfter;
      setInputValue(newValue);
      setShowSuggestions(false);

      setTimeout(() => {
        const newPos = replaceStart + suggestion.length + 1;
        textarea.setSelectionRange(newPos, newPos);
        textarea.focus();
      }, 0);
    };

    return (
      <div className="flex flex-col justify-center w-full relative mb-4">
        <textarea
          name="message"
          className={classNames(
            disabled
              ? "placeholder:text-gray-600 text-gray-800 dark:text-gray-400 dark:bg-gray-800 focus:ring-0"
              : "placeholder:text-gray-400 text-gray-900 dark:text-gray-200 dark:bg-gray-900",
            "block rounded-xl border p-4 shadow-sm sm:text-md sm:leading-6 resize-none dark:border-gray-600 pl-12 sm:pl-20 pr-12 overflow-y-hidden mr-1"
          )}
          style={{ height: "auto" }}
          rows={1}
          placeholder="Enter your message here..."
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyPress}
          ref={ref}
        />

        {showSuggestions && filteredSuggestions.length > 0 && (
          <ul className="absolute z-10 mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg text-sm w-full max-h-48 overflow-y-auto left-0 bottom-full">
            {filteredSuggestions.map((s) => (
              <li
                key={s}
                className="px-4 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-200"
                onClick={() => insertSuggestionAtCaret(s)}
              >
                {s}
              </li>
            ))}
          </ul>
        )}

        <div className="absolute left-0 top-0 w-full">
          <MessageSettingsPopup
            isShown={messageSettingsShown}
            setIsShown={setMessageSettingsShown}
            settingsCogRef={settingsCogRef}
          />
        </div>

        <div className="group absolute flex items-center left-0">
          <div
            ref={settingsCogRef}
            onClick={() => setMessageSettingsShown((prev) => !prev)}
            className="hover:cursor-pointer hover:bg-white/10 dark:text-gray-400 ml-2 p-1 rounded-md transition-all duration-150"
          >
            <Cog6ToothIcon className="hover:-rotate-6 h-6 w-6 [&>path]:stroke-[2]" />
          </div>
          <div className="dark:text-gray-400 ml-1 invisible sm:visible">
            {messageOptions?.secure_data ? (
              <ShieldCheckIcon className="h-6 w-6 text-green-500 [&>path]:stroke-[2]" />
            ) : (
              <ShieldExclamationIcon className="h-6 w-6 text-gray-400 [&>path]:stroke-[2]" />
            )}
          </div>
        </div>

        <div
          onClick={handleSubmit}
          className={classNames(
            inputValue.length > 0 && !disabled
              ? "dark:text-gray-700 dark:bg-gray-300 dark:hover:cursor-pointer"
              : "",
            "group absolute right-0 mr-4 -rotate-90 dark:text-gray-400 p-1 rounded-md transition-all duration-150"
          )}
        >
          <PaperAirplaneIcon
            className={classNames(
              inputValue.length > 0 ? "group-hover:-rotate-6" : "",
              "h-6 w-6 [&>path]:stroke-[2]"
            )}
          />
        </div>
      </div>
    );
  }
);

export default ExpandingInput;
