import { CreateDealForm } from "@/components/deals/create-deal-form";

export default function NewDealPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Create New Deal</h1>
      <CreateDealForm />
    </div>
  );
}
