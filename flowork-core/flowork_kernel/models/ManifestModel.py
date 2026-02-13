########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\ManifestModel.py total lines 58 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PropertyModel(BaseModel):
    id: str
    type: str
    label: str
    description: Optional[str] = ""
    default: Optional[Any] = None

class PortModel(BaseModel):
    name: str
    display_name: str
    tooltip: Optional[str] = ""

class OutputSchemaModel(BaseModel):
    name: str
    type: str
    description: Optional[str] = ""

class DisplayPropertiesModel(BaseModel):
    color: Optional[str] = ""
    text_color: Optional[str] = ""

class ManifestModel(BaseModel):
    id: str
    name: str
    author: str
    description: str
    type: str
    entry_point: str
    version: Optional[str] = "1.0"
    requires_input: Optional[bool] = True

    properties: List[PropertyModel] = Field(default_factory=list)
    output_ports: List[PortModel] = Field(default_factory=list)

    requires_services: List[str] = Field(default_factory=list)

    permissions: List[str] = Field(default_factory=list) # "filesystem.read", "network.outbound"
    provided_services: List[str] = Field(default_factory=list) # "pdf_generator", "email_sender"

    output_schema: List[OutputSchemaModel] = Field(default_factory=list)
    display_properties: Optional[DisplayPropertiesModel] = Field(default_factory=DisplayPropertiesModel)

    is_system: Optional[bool] = False
    config_ui_entry_point: Optional[str] = None
    is_service: Optional[bool] = False
    main_processor_file: Optional[str] = None
    dependencies_file: Optional[str] = None
    supported_languages: List[str] = Field(default_factory=list)
    is_paused: Optional[bool] = False
