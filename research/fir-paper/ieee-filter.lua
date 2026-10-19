local function trim(s)
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function tex_escape(s)
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("([%%&#_$%%{}])", "\\%1")
  s = s:gsub("~", "\\textasciitilde{}")
  s = s:gsub("%^", "\\textasciicircum{}")
  return s
end

function Pandoc(doc)
  local blocks, out = doc.blocks, pandoc.List()
  local i = 1
  local appendix_started = false
  while i <= #blocks do
    local b = blocks[i]
    if b.t == "Header" and b.level == 1 and b.identifier == "paper-title" then
      -- The title is supplied through metadata by the renderer.
    elseif b.t == "Header" and pandoc.utils.stringify(b.content):lower() == "abstract" then
      local body = pandoc.List()
      i = i + 1
      while i <= #blocks and not (blocks[i].t == "Header" and blocks[i].level <= b.level) do
        body:insert(blocks[i]); i = i + 1
      end
      out:insert(pandoc.RawBlock("latex", "\\begin{abstract}"))
      for _, item in ipairs(body) do out:insert(item) end
      out:insert(pandoc.RawBlock("latex", "\\end{abstract}"))
      goto continue
    elseif b.t == "Header" and pandoc.utils.stringify(b.content):lower() == "references" then
      out:insert(pandoc.RawBlock("latex", "\\begin{thebibliography}{99}"))
      i = i + 1
      local n = 0
      while i <= #blocks and blocks[i].t ~= "Header" do
        if blocks[i].t == "Para" or blocks[i].t == "Plain" then
          n = n + 1
          local inlines = pandoc.Inlines(blocks[i].content)
          if inlines[1] and inlines[1].t == "Str" then
            inlines[1].text = inlines[1].text:gsub("^%[%d+%]", "")
            if inlines[1].text == "" then inlines:remove(1) end
          end
          if inlines[1] and inlines[1].t == "Space" then inlines:remove(1) end
          local entry = pandoc.write(pandoc.Pandoc({pandoc.Para(inlines)}), "latex")
          entry = entry:gsub("\\par%s*$", "")
          out:insert(pandoc.RawBlock("latex", "\\bibitem{" .. tostring(n) .. "} " .. entry))
        else out:insert(blocks[i]) end
        i = i + 1
      end
      out:insert(pandoc.RawBlock("latex", "\\end{thebibliography}"))
      goto continue
    else
      if b.t == "Header" then
        local heading = pandoc.utils.stringify(b.content)
        local appendix_title = heading:match("^Appendix [A-Z]%.%s*(.*)$")
        if appendix_title then
          if not appendix_started then
            out:insert(pandoc.RawBlock("latex", "\\appendices"))
            appendix_started = true
          end
          heading = appendix_title
        end
        b.level = math.max(1, b.level - 1)
        heading = heading:gsub("^%s*%d[%d%.]*%s*", "")
        b.content = pandoc.Inlines(pandoc.Str(heading))
      end
      out:insert(b)
    end
    i = i + 1
    ::continue::
  end
  doc.blocks = out
  return doc
end

function CodeBlock(code)
  local out, ordinary = {}, {}
  local function flush()
    if #ordinary > 0 then
      local body = table.concat(ordinary, "\n"):gsub("\\end{Verbatim}", "\\end {Verbatim}")
      out[#out + 1] = "\\begin{Verbatim}[breaklines,breakanywhere,breaksymbolleft={},breaksymbolright={},fontsize=\\scriptsize]\n"
        .. body .. "\n\\end{Verbatim}"
      ordinary = {}
    end
  end
  for line in (code.text .. "\n"):gmatch("(.-)\n") do
    if line:match("^[0-9a-fA-F][0-9a-fA-F]+$") and #line >= 40 then
      flush()
      out[#out + 1] = "\\noindent\\texttt{\\scriptsize\\seqsplit{" .. line .. "}}\\par"
    else ordinary[#ordinary + 1] = line end
  end
  flush()
  return pandoc.RawBlock("latex", table.concat(out, "\n"))
end

function Para(p)
  if #p.content == 1 and p.content[1].t == "Image" then
    local image = p.content[1]
    local caption = pandoc.utils.stringify(image.caption)
    local label = image.identifier ~= "" and image.identifier or ("fig:" .. image.src:gsub("[^%w:.-]", "-"))
    local raw = "\\begin{figure*}[!t]\n\\centering\n\\includegraphics[width=\\textwidth]{" .. image.src .. "}\n"
      .. "\\caption{" .. tex_escape(caption) .. "}\\label{" .. tex_escape(label) .. "}\n\\end{figure*}"
    return pandoc.RawBlock("latex", raw)
  end
end

function Figure(f)
  local image
  for _, block in ipairs(f.content) do
    for _, inline in ipairs(block.content or {}) do
      if inline.t == "Image" then image = inline; break end
    end
    if image then break end
  end
  if image then
    local caption = pandoc.utils.stringify(f.caption.long)
    local label = image.identifier ~= "" and image.identifier or ("fig:" .. image.src:gsub("[^%w:.-]", "-"))
    local raw = "\\begin{figure*}[!t]\n\\centering\n\\includegraphics[width=\\textwidth]{" .. image.src .. "}\n"
      .. "\\caption{" .. tex_escape(caption) .. "}\\label{" .. tex_escape(label) .. "}\n\\end{figure*}"
    return pandoc.RawBlock("latex", raw)
  end
end

local table_count = 0
function Table(t)
  table_count = table_count + 1
  local ncols = #t.colspecs
  local col = ""
  for _ = 1, ncols do col = col .. ">{\\raggedright\\arraybackslash}X" end
  local rows = {}
  local function add_row(row)
    local cells = {}
    for _, cell in ipairs(row.cells) do
      local value = pandoc.write(pandoc.Pandoc(cell.contents), "latex")
      value = value:gsub("\\par%s*$", "")
      value = trim(value):gsub("\n+", " ")
      cells[#cells + 1] = value
    end
    rows[#rows + 1] = table.concat(cells, " & ") .. " " .. string.char(92, 92, 10)
  end
  for _, row in ipairs(t.head.rows) do add_row(row) end
  rows[#rows + 1] = "\\midrule\n"
  for _, body in ipairs(t.bodies) do
    for _, row in ipairs(body.head) do add_row(row) end
    for _, row in ipairs(body.body) do add_row(row) end
  end
  for _, row in ipairs(t.foot.rows) do add_row(row) end
  local caption = pandoc.write(pandoc.Pandoc(t.caption.long), "latex")
  caption = caption:gsub("\\par%s*$", "")
  local raw = "\\begin{table*}[!t]\n\\centering\\footnotesize\n"
  if trim(caption) ~= "" then
    local label = t.attr.identifier ~= "" and t.attr.identifier or ("tab:" .. tostring(table_count))
    raw = raw .. "\\caption{" .. trim(caption) .. "}\\label{" .. label .. "}\n"
  end
  raw = raw .. "\\begin{tabularx}{\\textwidth}{@{}" .. col .. "@{}}\n\\toprule\n"
    .. table.concat(rows) .. "\\bottomrule\n\\end{tabularx}\n"
  return pandoc.RawBlock("latex", raw .. "\\end{table*}")
end
