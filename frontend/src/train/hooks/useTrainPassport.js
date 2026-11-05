import { useQuery } from "@tanstack/react-query";
import api from "../../api/api";
import { formatToDB } from "../../utils/formatters";
import { resetTrainEquipment } from "../utils/caseFormData";

/** Загружает номера, вагоны и экземпляры выбранного поездного паспорта */
export function useTrainPassport(data, setData) {
  const passports = useQuery({
    queryKey: ["train-passports", data.train.train_model_id],
    queryFn: async () =>
      (
        await api.get("/train/passports", {
          params: { model_id: data.train.train_model_id },
        })
      ).data,
    enabled: !!data.train.train_model_id,
  });
  const passport = useQuery({
    queryKey: [
      "train-passport",
      data.passport_id,
      data.train.wagon_node_ids,
      formatToDB(data.fault_date) || null,
      data.id,
    ],
    queryFn: async () =>
      (
        await api.get(`/train/passports/${data.passport_id}`, {
          params: {
            wagon_node_ids: data.train.wagon_node_ids.join(","),
            fault_date: formatToDB(data.fault_date) || undefined,
            case_id: data.id || undefined,
          },
        })
      ).data,
    enabled: !!data.passport_id,
  });

  const selectModel = (value) =>
    setData((d) => ({
      ...resetTrainEquipment(d),
      passport_id: null,
      train: {
        train_model_id: value,
        wagon_node_ids: [],
        passport_node_ids: [],
      },
    }));
  const selectPassport = (value) =>
    setData((d) => ({
      ...resetTrainEquipment(d),
      passport_id: value,
      train: { ...resetTrainEquipment(d).train, wagon_node_ids: [] },
    }));
  const selectWagons = (ids) =>
    setData((d) => ({
      ...resetTrainEquipment(d),
      train: { ...resetTrainEquipment(d).train, wagon_node_ids: ids },
    }));
  return { passports, passport, selectModel, selectPassport, selectWagons };
}
