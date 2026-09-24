import { useState } from "react";
import { ArrowLeft, BookOpenText, SearchX } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { PassportSearch } from "../components/productPassports/PassportSearch";
import { PassportTree } from "../components/productPassports/PassportTree";
import {
  useProductPassport,
  useProductPassportModels,
} from "../hooks/api/useProductPassportsApi";

export default function ProductPassportsPage() {
  const navigate = useNavigate();
  const [selectedModelId, setSelectedModelId] = useState(null);
  const [selectedPassportId, setSelectedPassportId] = useState(null);
  const {
    data: models = [],
    isLoading: modelsLoading,
    isError: modelsError,
  } = useProductPassportModels();
  const {
    data: passport,
    isLoading: passportLoading,
    isError: passportError,
  } = useProductPassport(selectedPassportId);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-4 border-b border-gray-200 bg-white px-6 py-4">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Назад</span>
        </button>
        <h1 className="text-xl font-semibold text-gray-900">
          Паспорта изделий
        </h1>
      </div>

      <div className="flex min-h-0 flex-1 flex-col overflow-auto bg-gray-50 p-6">
        <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5">
          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                <BookOpenText className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-black text-slate-900">
                  Поиск паспорта
                </h2>
                <p className="text-xs text-slate-500">
                  Выберите модель и найдите локомотив по номеру
                </p>
              </div>
            </div>

            {modelsLoading ? (
              <div className="flex h-20 items-center justify-center gap-3 text-xs font-black tracking-wider text-slate-400 uppercase">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
                Загрузка моделей...
              </div>
            ) : modelsError ? (
              <div className="rounded-lg bg-red-50 px-4 py-3 text-sm font-semibold text-red-600">
                Не удалось загрузить модели локомотивов
              </div>
            ) : (
              <PassportSearch
                models={models}
                selectedModelId={selectedModelId}
                onModelChange={setSelectedModelId}
                onPassportSelect={setSelectedPassportId}
              />
            )}
          </section>

          {passportLoading ? (
            <div className="flex min-h-64 flex-1 flex-col items-center justify-center gap-4 rounded-xl border border-gray-200 bg-white">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
              <span className="text-xs font-black tracking-widest text-slate-400 uppercase">
                Загрузка паспорта...
              </span>
            </div>
          ) : passportError ? (
            <div className="rounded-xl border border-red-100 bg-red-50 p-5 text-sm font-semibold text-red-600">
              Не удалось загрузить паспорт
            </div>
          ) : passport ? (
            <PassportTree key={passport.id} passport={passport} />
          ) : (
            <div className="flex min-h-64 flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 text-slate-400">
                <SearchX className="h-6 w-6" />
              </div>
              <p className="text-sm font-bold text-slate-600">
                Выберите паспорт для просмотра
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Данные появятся после выбора точного номера локомотива
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
