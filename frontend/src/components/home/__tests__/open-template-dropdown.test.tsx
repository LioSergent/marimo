/* Copyright 2026 Marimo. All rights reserved. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "jotai";
import type React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MockRequestClient } from "@/__mocks__/requests";
import { requestClientAtom } from "@/core/network/requests";
import { store } from "@/core/state/jotai";
import { openNotebook } from "@/utils/links";
import { OpenTemplateDropDown } from "../components";

vi.mock("@/utils/links", () => ({
  openNotebook: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <Provider store={store}>{children}</Provider>
);

const TEMPLATE = {
  name: "analysis.py",
  path: "/templates/analysis.py",
  displayName: "analysis",
  description: "Load data and plot it",
};

describe("OpenTemplateDropDown", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when no templates are configured", async () => {
    const client = MockRequestClient.create();
    store.set(requestClientAtom, client);

    const { container } = render(<OpenTemplateDropDown />, { wrapper });

    await waitFor(() => expect(client.getTemplates).toHaveBeenCalled());
    expect(container.firstChild).toBeNull();
  });

  it("opens a new notebook from the selected template", async () => {
    const client = MockRequestClient.create({
      getTemplates: vi.fn().mockResolvedValue({ files: [TEMPLATE] }),
      openTemplate: vi
        .fn()
        .mockResolvedValue({ name: "analysis.py", path: "__new__abc" }),
    });
    store.set(requestClientAtom, client);

    render(<OpenTemplateDropDown />, { wrapper });

    const trigger = await screen.findByTestId("open-template-button");
    fireEvent.keyDown(trigger, { key: "Enter" });

    expect(await screen.findByText("analysis")).toBeInTheDocument();
    expect(screen.getByText("Load data and plot it")).toBeInTheDocument();

    fireEvent.click(screen.getByText("analysis"));

    await waitFor(() =>
      expect(openNotebook).toHaveBeenCalledWith("__new__abc"),
    );
    expect(client.openTemplate).toHaveBeenCalledWith({
      templatePath: "/templates/analysis.py",
    });
  });
});
